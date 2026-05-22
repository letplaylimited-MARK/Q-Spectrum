"""
Q-SpecTrum File Operations Module
Real filesystem operations bridge for the project management platform.

This module provides safe, intelligent file system operations for Q-SpecTrum,
enabling AI roles to read, write, and analyze project files while respecting
security boundaries and respecting .gitignore patterns.

Author: Q-SpecTrum Team
"""

import difflib
import fnmatch
import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("q-spectrum.file-ops")


@dataclass
class FileInfo:
    """Metadata for a single file."""
    path: str
    rel_path: str
    size: int
    modified_time: float
    extension: str
    is_text: bool
    line_count: Optional[int] = None
    hash_md5: Optional[str] = None


@dataclass
class DirectoryNode:
    """Tree structure node for a directory."""
    name: str
    path: str
    rel_path: str
    size: int
    file_count: int
    dir_count: int
    children: List['DirectoryNode']
    files: List[FileInfo]


class GitignoreParser:
    """Parse and match .gitignore patterns."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.patterns: List[Tuple[str, bool]] = []
        self._load_gitignore()

    def _load_gitignore(self) -> None:
        """Load .gitignore file if it exists."""
        gitignore_path = self.project_root / '.gitignore'
        if not gitignore_path.exists():
            return

        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Separate negation patterns
                        negation = line.startswith('!')
                        if negation:
                            line = line[1:]
                        self.patterns.append((line, negation))
            logger.debug(f"加载 .gitignore 成功 | Loaded {len(self.patterns)} patterns from .gitignore")
        except Exception as e:
            logger.warning(f"无法读取 .gitignore: {e} | Failed to read .gitignore: {e}")

    def should_ignore(self, rel_path: str, is_dir: bool = False) -> bool:
        """Check if a path should be ignored."""
        parts = Path(rel_path).parts

        # Check each pattern
        ignore = False
        for pattern, negation in self.patterns:
            # Handle directory-only patterns
            if pattern.endswith('/'):
                if not is_dir:
                    continue
                pattern = pattern.rstrip('/')

            # Match against path and filename
            if fnmatch.fnmatch(rel_path, pattern) or any(
                fnmatch.fnmatch(part, pattern) for part in parts
            ):
                ignore = not negation

        return ignore


class FileScanner:
    """Scan project directory and return structured file tree."""

    # Default text file extensions
    TEXT_EXTENSIONS = {
        '.py', '.js', '.ts', '.tsx', '.jsx', '.md', '.txt', '.json',
        '.yaml', '.yml', '.csv', '.html', '.css', '.scss', '.less',
        '.sql', '.sh', '.bat', '.java', '.cpp', '.c', '.h', '.go',
        '.rs', '.rb', '.php', '.xml', '.svg', '.env', '.env.example',
        '.conf', '.config', '.ini', '.toml', '.gradle', '.maven',
        '.lock', '.gitignore', '.dockerignore', '.eslintrc',
        '.prettierrc', '.babelrc', '.editorconfig', 'Dockerfile',
        'Makefile', 'README', 'LICENSE', 'CHANGELOG'
    }

    # Directories to always skip (performance + irrelevant)
    SKIP_DIRS = {
        '__pycache__', 'node_modules', '.git', '.svn', '.hg',
        'venv', '.venv', 'env', '.env', '.tox', '.mypy_cache',
        '.pytest_cache', 'dist', 'build', 'egg-info',
        '.eggs', '.cache', '.tmp', 'tmp',
        'Archive', 'archive', 'ARCHIVE', '_ARCHIVE',
        'AI项目管理',  # Legacy management tree (2400+ files)
    }

    # Maximum files to scan before early-exit (prevents timeout on huge folders)
    MAX_FILES = 1000

    # Maximum seconds for a full scan (wall-clock safety net)
    MAX_SCAN_SECONDS = 4.0

    def __init__(self, project_root: str, max_depth: int = 20):
        self.project_root = Path(project_root).resolve()
        self.max_depth = max_depth
        self.gitignore_parser = GitignoreParser(str(self.project_root))
        self._scan_start: float = 0.0  # set at scan() time

        if not self.project_root.exists():
            raise ValueError(f"项目根目录不存在 | Project root does not exist: {self.project_root}")

    def scan(self) -> Tuple[List[FileInfo], DirectoryNode]:
        """
        Scan the project directory.

        Returns:
            Tuple of (flat file list, directory tree)
        """
        import time
        self._scan_start = time.time()
        file_list = []
        tree = self._scan_dir(self.project_root, '', 0, file_list)
        elapsed = time.time() - self._scan_start
        logger.info(f"扫描完成: {len(file_list)} 个文件, 耗时 {elapsed:.1f}s | Scan complete: {len(file_list)} files in {elapsed:.1f}s")
        return file_list, tree

    def _scan_dir(
        self, dir_path: Path, rel_path: str, depth: int, file_list: List[FileInfo]
    ) -> DirectoryNode:
        """Recursively scan directory."""
        if depth > self.max_depth:
            logger.debug(f"到达最大深度 | Max depth reached: {rel_path}")
            return DirectoryNode(
                name=dir_path.name or '/',
                path=str(dir_path),
                rel_path=rel_path or '/',
                size=0,
                file_count=0,
                dir_count=0,
                children=[],
                files=[]
            )

        node = DirectoryNode(
            name=dir_path.name or '/',
            path=str(dir_path),
            rel_path=rel_path or '/',
            size=0,
            file_count=0,
            dir_count=0,
            children=[],
            files=[]
        )

        import time as _time

        try:
            # Use os.scandir for performance — avoids expensive stat() calls
            raw_entries = list(os.scandir(str(dir_path)))
        except PermissionError:
            logger.warning(f"权限被拒绝 | Permission denied: {dir_path}")
            return node

        # Pre-filter hidden entries BEFORE classification (huge perf win when
        # thousands of .fuse_hidden* or other dotfiles exist)
        KEEP_HIDDEN = {'.gitignore', '.env', '.env.example'}
        visible = [de for de in raw_entries
                   if not de.name.startswith('.') or de.name in KEEP_HIDDEN]

        # Separate dirs and files using cached DirEntry.is_dir (no extra stat)
        dir_entries = []
        file_entries = []
        for de in visible:
            try:
                if de.is_dir(follow_symlinks=False):
                    dir_entries.append(de)
                elif de.is_file(follow_symlinks=False):
                    file_entries.append(de)
            except OSError:
                continue
        # Process dirs first, then files (same semantic order as before, but no sort)
        all_entries = dir_entries + file_entries

        for de in all_entries:
            # Early exit: file count limit
            if len(file_list) >= self.MAX_FILES:
                break
            # Early exit: wall-clock time limit
            if self._scan_start and (_time.time() - self._scan_start) > self.MAX_SCAN_SECONDS:
                logger.warning(f"Scan time limit ({self.MAX_SCAN_SECONDS}s) reached at {len(file_list)} files")
                break

            entry_name = de.name

            rel = str(Path(rel_path) / entry_name) if rel_path else entry_name
            entry = Path(de.path)

            if de.is_dir(follow_symlinks=False):
                # Skip known heavy/irrelevant directories
                if entry_name in self.SKIP_DIRS:
                    continue
                if self.gitignore_parser.should_ignore(rel, is_dir=True):
                    continue

                child = self._scan_dir(entry, rel, depth + 1, file_list)
                node.children.append(child)
                node.dir_count += 1
                node.size += child.size
            else:
                if self.gitignore_parser.should_ignore(rel, is_dir=False):
                    continue

                try:
                    file_info = self._get_file_info(entry, rel, quick=True)
                    node.files.append(file_info)
                    file_list.append(file_info)
                    node.file_count += 1
                    node.size += file_info.size
                except Exception as e:
                    logger.warning(f"无法读取文件信息 | Failed to get file info {entry}: {e}")

        return node

    def _get_file_info(self, file_path: Path, rel_path: str,
                       quick: bool = False) -> FileInfo:
        """Extract metadata from a file.

        Args:
            quick: If True, skip line counting and binary detection (fast scan mode).
        """
        stat = file_path.stat()
        extension = file_path.suffix.lower()

        # Determine if file is text (extension-only in quick mode)
        is_text = self._is_text_file(file_path, extension, quick=quick)

        line_count = None
        if is_text and not quick:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    line_count = sum(1 for _ in f)
            except Exception:
                line_count = None

        return FileInfo(
            path=str(file_path),
            rel_path=rel_path,
            size=stat.st_size,
            modified_time=stat.st_mtime,
            extension=extension,
            is_text=is_text,
            line_count=line_count
        )

    def _is_text_file(self, file_path: Path, extension: str,
                      quick: bool = False) -> bool:
        """Determine if file is text based on extension and content.

        Args:
            quick: If True, only use extension matching (no file I/O).
        """
        if extension in self.TEXT_EXTENSIONS:
            return True

        # Check without extension
        if file_path.name in self.TEXT_EXTENSIONS:
            return True

        if quick:
            return False  # Unknown extension → assume binary in quick mode

        # Try binary detection for unknown files
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(512)
                return b'\x00' not in chunk
        except Exception:
            return False


class FileReader:
    """Read file contents with smart handling."""

    ENCODINGS = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin-1']
    DEFAULT_LIMIT = 50 * 1024  # 50 KB

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()

    def read(
        self, file_path: str, line_start: Optional[int] = None,
        line_end: Optional[int] = None, byte_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Read file with smart handling.

        Args:
            file_path: Relative or absolute path
            line_start: Start line number (1-indexed)
            line_end: End line number (inclusive)
            byte_limit: Maximum bytes to read (default 50KB)

        Returns:
            Dict with 'content', 'encoding', 'truncated', 'line_count', etc.
        """
        file_path = self._validate_path(file_path)
        byte_limit = byte_limit or self.DEFAULT_LIMIT

        if not file_path.exists():
            return {'error': f'文件不存在 | File not found: {file_path}'}

        if file_path.is_dir():
            return {'error': f'路径是目录 | Path is directory: {file_path}'}

        stat = file_path.stat()

        # Binary file handling
        if not self._is_text_file(file_path):
            return {
                'path': str(file_path),
                'type': 'binary',
                'size': stat.st_size,
                'modified_time': stat.st_mtime,
                'hash_md5': self._compute_hash(file_path),
                'truncated': False
            }

        # Text file handling
        try:
            content = self._read_text_file(file_path, byte_limit)
            lines = content.split('\n')

            # Apply line range if specified
            if line_start is not None or line_end is not None:
                start = (line_start or 1) - 1
                end = (line_end or len(lines))
                lines = lines[start:end]
                content = '\n'.join(lines)

            return {
                'path': str(file_path),
                'type': 'text',
                'content': content,
                'encoding': 'utf-8',
                'size': stat.st_size,
                'modified_time': stat.st_mtime,
                'line_count': len(lines),
                'truncated': stat.st_size > byte_limit
            }
        except Exception as e:
            logger.error(f"无法读取文本文件 | Failed to read text file {file_path}: {e}")
            return {'error': f'读取失败 | Read failed: {str(e)}'}

    def _validate_path(self, file_path: str) -> Path:
        """Validate path is within project root (security check)."""
        path = Path(file_path).resolve()

        if not str(path).startswith(str(self.project_root)):
            # Try relative to project root
            path = (self.project_root / file_path).resolve()

        if not str(path).startswith(str(self.project_root)):
            raise ValueError(f"路径越界 | Path traversal attack detected: {file_path}")

        return path

    def _read_text_file(self, file_path: Path, byte_limit: int) -> str:
        """Read text file with encoding detection."""
        for encoding in self.ENCODINGS:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read(byte_limit)
                    logger.debug(f"使用编码 {encoding} | Read with encoding {encoding}")
                    return content
            except (UnicodeDecodeError, LookupError):
                continue

        # Fallback: read with errors ignored
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read(byte_limit)

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is text."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(512)
                return b'\x00' not in chunk
        except Exception:
            return False

    def _compute_hash(self, file_path: Path) -> str:
        """Compute MD5 hash of file."""
        md5 = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception:
            return None


class FileWriter:
    """Write and modify files safely."""

    def __init__(self, project_root: str, auto_backup: bool = True):
        self.project_root = Path(project_root).resolve()
        self.auto_backup = auto_backup

    def write(self, file_path: str, content: str, append: bool = False) -> Dict[str, Any]:
        """
        Write to file safely with backup.

        Args:
            file_path: Relative or absolute path
            content: Content to write
            append: Append mode if True, overwrite if False

        Returns:
            Dict with operation status and diff summary
        """
        file_path = self._validate_path(file_path)

        # Create directories
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create backup if file exists
        old_content = None
        if file_path.exists() and self.auto_backup:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    old_content = f.read()

                backup_path = Path(str(file_path) + '.bak')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(old_content)
                logger.info(f"备份文件 | Backup created: {backup_path}")
            except Exception as e:
                logger.warning(f"无法创建备份 | Failed to create backup: {e}")

        # Handle append mode
        if append and file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    old_content = f.read()
                content = old_content + content
            except Exception:
                pass

        # Write file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"文件已写入 | File written: {file_path}")

            # Generate diff
            diff_summary = ''
            if old_content:
                diff_lines = list(difflib.unified_diff(
                    old_content.splitlines(keepends=True),
                    content.splitlines(keepends=True),
                    fromfile='original',
                    tofile='modified',
                    lineterm=''
                ))
                diff_summary = ''.join(diff_lines[:20])  # Limit diff output

            return {
                'success': True,
                'path': str(file_path),
                'size': len(content),
                'diff_preview': diff_summary,
                'message': '写入成功 | File written successfully'
            }
        except Exception as e:
            logger.error(f"写入失败 | Write failed {file_path}: {e}")
            return {'success': False, 'error': f'写入失败 | Write failed: {str(e)}'}

    def _validate_path(self, file_path: str) -> Path:
        """Validate path is within project root."""
        path = Path(file_path).resolve()

        if not str(path).startswith(str(self.project_root)):
            path = (self.project_root / file_path).resolve()

        if not str(path).startswith(str(self.project_root)):
            raise ValueError(f"路径越界 | Path traversal attack detected: {file_path}")

        return path


class ProjectAnalyzer:
    """Analyze project structure and characteristics."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.scanner = FileScanner(project_root)

    def analyze(self) -> Dict[str, Any]:
        """
        Analyze the entire project.

        Returns:
            Dict with statistics and analysis
        """
        files, tree = self.scanner.scan()

        return {
            'root': str(self.project_root),
            'total_files': len(files),
            'total_size': tree.size,
            'file_counts': self._count_by_extension(files),
            'total_lines': self._count_total_lines(files),
            'project_type': self._detect_project_type(files),
            'key_files': self._find_key_files(files),
            'tree': self._tree_to_dict(tree),
            'scanned_at': datetime.now().isoformat()
        }

    def _count_by_extension(self, files: List[FileInfo]) -> Dict[str, int]:
        """Count files by extension."""
        counts = {}
        for f in files:
            ext = f.extension or 'no_ext'
            counts[ext] = counts.get(ext, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: -x[1]))

    def _count_total_lines(self, files: List[FileInfo]) -> int:
        """Count total lines in all text files."""
        return sum(f.line_count or 0 for f in files if f.is_text)

    def _detect_project_type(self, files: List[FileInfo]) -> str:
        """Detect project type by key files."""
        file_names = {f.rel_path for f in files}

        if any('package.json' in fn for fn in file_names):
            return 'node'
        if any('requirements.txt' in fn or 'setup.py' in fn or 'pyproject.toml' in fn for fn in file_names):
            return 'python'
        if any('pom.xml' in fn or 'build.gradle' in fn for fn in file_names):
            return 'java'
        if any('go.mod' in fn for fn in file_names):
            return 'go'
        if any('Cargo.toml' in fn for fn in file_names):
            return 'rust'

        # Check by file extensions
        py_count = sum(1 for f in files if f.extension == '.py')
        js_count = sum(1 for f in files if f.extension in {'.js', '.ts'})
        java_count = sum(1 for f in files if f.extension == '.java')

        if py_count > js_count and py_count > java_count:
            return 'python'
        if js_count > py_count:
            return 'node'
        if java_count > 0:
            return 'java'

        return 'mixed'

    def _find_key_files(self, files: List[FileInfo]) -> List[str]:
        """Find key files like README, package.json, etc."""
        key_names = {
            'README.md', 'README.txt', 'README',
            'package.json', 'requirements.txt', 'setup.py', 'pyproject.toml',
            'pom.xml', 'build.gradle', 'Dockerfile', 'docker-compose.yml',
            '.gitignore', 'Makefile', 'LICENSE', 'CHANGELOG.md'
        }

        found = []
        for f in files:
            if f.rel_path in key_names or Path(f.rel_path).name in key_names:
                found.append(f.rel_path)

        return sorted(found)

    def _tree_to_dict(self, node: DirectoryNode) -> Dict[str, Any]:
        """Convert tree to dict for JSON serialization."""
        return {
            'name': node.name,
            'rel_path': node.rel_path,
            'size': node.size,
            'file_count': node.file_count,
            'dir_count': node.dir_count,
            'children': [self._tree_to_dict(child) for child in node.children],
            'file_list': [asdict(f) for f in node.files]
        }


class FileOps:
    """Main file operations interface."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.scanner = FileScanner(project_root)
        self.reader = FileReader(project_root)
        self.writer = FileWriter(project_root)
        self.analyzer = ProjectAnalyzer(project_root)

        logger.info(f"初始化文件操作 | FileOps initialized for {self.project_root}")

    def scan_directory(self) -> Dict[str, Any]:
        """Scan project directory."""
        files, tree = self.scanner.scan()
        return {
            'files': [asdict(f) for f in files],
            'tree': self._tree_to_dict(tree)
        }

    def read_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Read file contents."""
        return self.reader.read(file_path, **kwargs)

    def write_file(self, file_path: str, content: str, **kwargs) -> Dict[str, Any]:
        """Write file contents."""
        return self.writer.write(file_path, content, **kwargs)

    def analyze_project(self) -> Dict[str, Any]:
        """Analyze project structure."""
        return self.analyzer.analyze()

    def _tree_to_dict(self, node: DirectoryNode) -> Dict[str, Any]:
        """Convert tree to dict."""
        return self.analyzer._tree_to_dict(node)


# Singleton factory
_file_ops_instances: Dict[str, FileOps] = {}


def get_file_ops(project_root: str) -> FileOps:
    """
    Get or create FileOps singleton for a project.

    Args:
        project_root: Path to project root directory

    Returns:
        FileOps instance
    """
    project_root = str(Path(project_root).resolve())

    if project_root not in _file_ops_instances:
        _file_ops_instances[project_root] = FileOps(project_root)
        logger.info(f"创建新实例 | Created FileOps instance for {project_root}")

    return _file_ops_instances[project_root]


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test with current directory
    ops = get_file_ops('.')
    analysis = ops.analyze_project()
    print(json.dumps({
        'total_files': analysis['total_files'],
        'total_size': analysis['total_size'],
        'project_type': analysis['project_type'],
        'key_files': analysis['key_files']
    }, indent=2))
