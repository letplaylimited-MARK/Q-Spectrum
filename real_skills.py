#!/usr/bin/env python3
"""
Real (non-mock) skill executors for Q-SpecTrum system operations.
Q-SpecTrum 系统操作的真实（非模拟）技能执行器。

Implements executable skills that perform actual system operations including file processing,
data analysis, and report generation without external LLM APIs. Provides structured input/output
handling using only Python stdlib, enabling standalone operation within Q-SpecTrum.
"""

import csv
import io
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path


class RealSkillExecutor:
    """
    Executes real skills that produce actual results.
    Falls through to LLM-based skills when no real executor matches.
    """

    def __init__(self, db_path=None, project_root=None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.db_path = db_path
        self._skills = {
            "file-analyzer": self.skill_file_analyzer,
            "data-processor": self.skill_data_processor,
            "code-reviewer": self.skill_code_reviewer,
            "project-planner": self.skill_project_planner,
            "system-reporter": self.skill_system_reporter,
        }

    def can_execute(self, skill_name: str) -> bool:
        """Check if we have a real executor for this skill."""
        return skill_name.lower() in self._skills

    def list_real_skills(self) -> list:
        """List all real executable skills."""
        return [
            {"key": "file-analyzer", "name": "File Analyzer",
             "description": "Analyze file structure, count lines, detect encoding, extract metadata"},
            {"key": "data-processor", "name": "Data Processor",
             "description": "Parse CSV/JSON files, compute statistics, find patterns"},
            {"key": "code-reviewer", "name": "Code Reviewer",
             "description": "Analyze Python files for complexity, issues, and patterns"},
            {"key": "project-planner", "name": "Project Planner",
             "description": "Break requirements into structured phases, tasks, and milestones"},
            {"key": "system-reporter", "name": "System Reporter",
             "description": "Generate comprehensive system status report from database"},
        ]

    def execute(self, skill_name: str, user_message: str, **kwargs) -> dict:
        """Execute a real skill."""
        fn = self._skills.get(skill_name.lower())
        if not fn:
            return {"status": "error", "error": f"No real executor for '{skill_name}'"}
        try:
            return fn(user_message, **kwargs)
        except Exception as e:
            return {"status": "error", "error": str(e), "skill": skill_name}

    # ── Skill 1: File Analyzer ────────────────────────────────

    def skill_file_analyzer(self, user_message: str, **kwargs) -> dict:
        """Analyze files in the project directory."""
        target = kwargs.get("file_path")

        # If no specific file, analyze project structure
        if not target:
            return self._analyze_project_structure()

        path = Path(target) if Path(target).is_absolute() else self.project_root / target
        if not path.exists():
            return {"status": "error", "error": f"File not found: {path}"}

        if path.is_dir():
            return self._analyze_directory(path)
        else:
            return self._analyze_single_file(path)

    def _analyze_project_structure(self) -> dict:
        """Analyze the Q-SpecTrum project structure (root level + 1 depth only for speed)."""
        root = self.project_root
        stats = {"total_files": 0, "total_dirs": 0, "by_extension": Counter(),
                 "total_lines": 0, "total_size": 0, "key_files": []}

        # Only scan root + 1 level deep to avoid slow FUSE rglob
        scan_items = list(root.iterdir())
        for subdir in list(scan_items):
            if subdir.is_dir() and not subdir.name.startswith('.'):
                try:
                    scan_items.extend(list(subdir.iterdir())[:50])
                except (PermissionError, OSError):
                    pass

        for item in scan_items:
            if item.is_file():
                stats["total_files"] += 1
                stats["by_extension"][item.suffix.lower()] += 1
                stats["total_size"] += item.stat().st_size
                if item.suffix in (".py", ".md", ".html", ".js", ".css"):
                    try:
                        lines = len(item.read_text(errors="ignore").splitlines())
                        stats["total_lines"] += lines
                        if lines > 100:
                            stats["key_files"].append({"name": str(item.relative_to(root)),
                                                       "lines": lines, "size": item.stat().st_size})
                    except Exception:
                        pass
            elif item.is_dir():
                stats["total_dirs"] += 1

        stats["key_files"].sort(key=lambda x: x["lines"], reverse=True)
        ext_summary = dict(stats["by_extension"].most_common(15))

        report = (
            f"## Project Structure Analysis\n\n"
            f"**Root**: {root.name}\n"
            f"**Total Files**: {stats['total_files']} | **Directories**: {stats['total_dirs']}\n"
            f"**Total Size**: {stats['total_size'] / 1024 / 1024:.1f} MB\n"
            f"**Code Lines**: {stats['total_lines']:,}\n\n"
            f"### File Types\n"
        )
        for ext, count in sorted(ext_summary.items(), key=lambda x: -x[1]):
            report += f"- `{ext or '(no ext)'}`: {count} files\n"

        report += "\n### Largest Files (by lines)\n"
        for f in stats["key_files"][:10]:
            report += f"- `{f['name']}`: {f['lines']:,} lines ({f['size'] / 1024:.0f} KB)\n"

        return {"status": "ok", "skill": "file-analyzer", "response": report,
                "data": {"total_files": stats["total_files"], "total_lines": stats["total_lines"]}}

    def _analyze_directory(self, path: Path) -> dict:
        files = list(path.iterdir())
        report = f"## Directory: {path.name}\n\n"
        report += f"**Items**: {len(files)}\n\n"
        for f in sorted(files, key=lambda x: (x.is_file(), x.name)):
            if f.is_dir():
                report += f"- [DIR] {f.name}/\n"
            else:
                report += f"- {f.name} ({f.stat().st_size / 1024:.1f} KB)\n"
        return {"status": "ok", "skill": "file-analyzer", "response": report}

    def _analyze_single_file(self, path: Path) -> dict:
        size = path.stat().st_size
        ext = path.suffix.lower()
        report = f"## File Analysis: {path.name}\n\n"
        report += f"- **Size**: {size / 1024:.1f} KB\n"
        report += f"- **Extension**: {ext}\n"
        report += f"- **Modified**: {datetime.fromtimestamp(path.stat().st_mtime).isoformat()}\n"

        if ext in (".py", ".md", ".txt", ".html", ".js", ".css", ".json", ".yaml", ".yml", ".csv"):
            try:
                content = path.read_text(errors="ignore")
                lines = content.splitlines()
                report += f"- **Lines**: {len(lines)}\n"
                report += f"- **Characters**: {len(content):,}\n"

                if ext == ".py":
                    funcs = [l.strip() for l in lines if l.strip().startswith("def ")]
                    classes = [l.strip() for l in lines if l.strip().startswith("class ")]
                    imports = [l.strip() for l in lines if l.strip().startswith("import ") or l.strip().startswith("from ")]
                    report += f"- **Classes**: {len(classes)}\n"
                    report += f"- **Functions**: {len(funcs)}\n"
                    report += f"- **Imports**: {len(imports)}\n"
                elif ext == ".md":
                    headers = [l for l in lines if l.startswith("#")]
                    report += f"- **Headers**: {len(headers)}\n"
                elif ext == ".json":
                    data = json.loads(content)
                    report += f"- **Type**: {type(data).__name__}\n"
                    if isinstance(data, dict):
                        report += f"- **Keys**: {len(data)}\n"
                    elif isinstance(data, list):
                        report += f"- **Items**: {len(data)}\n"
            except Exception as e:
                report += f"- **Read Error**: {e}\n"

        return {"status": "ok", "skill": "file-analyzer", "response": report}

    # ── Skill 2: Data Processor ───────────────────────────────

    def skill_data_processor(self, user_message: str, **kwargs) -> dict:
        """Process CSV or JSON data and compute statistics."""
        file_path = kwargs.get("file_path")
        data = kwargs.get("data")

        if file_path:
            path = Path(file_path) if Path(file_path).is_absolute() else self.project_root / file_path
            if not path.exists():
                return {"status": "error", "error": f"File not found: {path}"}
            try:
                content = path.read_text(errors="ignore")
            except Exception as e:
                return {"status": "error", "error": str(e)}

            if path.suffix.lower() == ".csv":
                return self._process_csv(content, path.name)
            elif path.suffix.lower() == ".json":
                return self._process_json(content, path.name)
            else:
                return {"status": "error", "error": f"Unsupported format: {path.suffix}"}

        if data:
            if isinstance(data, str):
                try:
                    parsed = json.loads(data)
                    return self._process_json(data, "inline-data")
                except json.JSONDecodeError:
                    return self._process_csv(data, "inline-data")
            elif isinstance(data, (list, dict)):
                return self._process_json(json.dumps(data), "inline-data")

        return {"status": "error", "error": "Provide file_path or data parameter"}

    def _process_csv(self, content: str, filename: str) -> dict:
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        if not rows:
            return {"status": "error", "error": "Empty CSV"}

        headers = rows[0]
        data_rows = rows[1:]

        report = f"## CSV Analysis: {filename}\n\n"
        report += f"- **Columns**: {len(headers)}\n"
        report += f"- **Rows**: {len(data_rows)}\n"
        report += f"- **Headers**: {', '.join(headers)}\n\n"

        # Per-column analysis
        report += "### Column Statistics\n\n"
        for i, header in enumerate(headers):
            values = [r[i] for r in data_rows if i < len(r) and r[i].strip()]
            unique = len(set(values))
            empty = len(data_rows) - len(values)

            # Try numeric analysis
            numeric = []
            for v in values:
                try:
                    numeric.append(float(v.replace(",", "")))
                except (ValueError, TypeError):
                    pass

            report += f"**{header}**: {len(values)} values, {unique} unique"
            if empty:
                report += f", {empty} empty"
            if numeric and len(numeric) > 1:
                avg = sum(numeric) / len(numeric)
                mn, mx = min(numeric), max(numeric)
                report += f"\n  - Range: {mn:.2f} ~ {mx:.2f} | Mean: {avg:.2f}"
            report += "\n\n"

        return {"status": "ok", "skill": "data-processor", "response": report,
                "data": {"columns": len(headers), "rows": len(data_rows)}}

    def _process_json(self, content: str, filename: str) -> dict:
        data = json.loads(content)
        report = f"## JSON Analysis: {filename}\n\n"
        report += f"- **Type**: {type(data).__name__}\n"

        if isinstance(data, dict):
            report += f"- **Keys**: {len(data)}\n"
            report += f"- **Key List**: {', '.join(list(data.keys())[:20])}\n\n"
            for key, val in list(data.items())[:10]:
                vtype = type(val).__name__
                if isinstance(val, (list, dict)):
                    report += f"- `{key}`: {vtype} ({len(val)} items)\n"
                else:
                    report += f"- `{key}`: {vtype} = {str(val)[:60]}\n"
        elif isinstance(data, list):
            report += f"- **Items**: {len(data)}\n"
            if data and isinstance(data[0], dict):
                keys = set()
                for item in data[:50]:
                    keys.update(item.keys())
                report += f"- **Fields**: {', '.join(sorted(keys))}\n"

        return {"status": "ok", "skill": "data-processor", "response": report}

    # ── Skill 3: Code Reviewer ────────────────────────────────

    def skill_code_reviewer(self, user_message: str, **kwargs) -> dict:
        """Analyze Python code for complexity, patterns, and potential issues."""
        file_path = kwargs.get("file_path")
        if not file_path:
            # Review all main Python files in project
            return self._review_project_code()

        path = Path(file_path) if Path(file_path).is_absolute() else self.project_root / file_path
        if not path.exists():
            return {"status": "error", "error": f"File not found: {path}"}
        return self._review_single_file(path)

    def _review_project_code(self) -> dict:
        """Review all Python files in the project."""
        root = self.project_root
        py_files = sorted(root.glob("*.py"))  # Only root level

        report = "## Code Review: Q-SpecTrum Python Files\n\n"
        total_lines = 0
        total_funcs = 0
        total_classes = 0
        issues = []

        for f in py_files:
            try:
                content = f.read_text(errors="ignore")
                lines = content.splitlines()
                funcs = len([l for l in lines if l.strip().startswith("def ")])
                classes = len([l for l in lines if l.strip().startswith("class ")])
                total_lines += len(lines)
                total_funcs += funcs
                total_classes += classes

                # Check for common issues
                for i, line in enumerate(lines, 1):
                    if "except:" in line and "Exception" not in line:
                        issues.append(f"`{f.name}:{i}` — bare except clause")
                    if len(line) > 200:
                        issues.append(f"`{f.name}:{i}` — line too long ({len(line)} chars)")
                    if "TODO" in line or "FIXME" in line or "HACK" in line:
                        issues.append(f"`{f.name}:{i}` — {line.strip()[:80]}")

                report += f"- **{f.name}**: {len(lines):,} lines, {classes} classes, {funcs} functions\n"
            except Exception:
                report += f"- **{f.name}**: (could not read)\n"

        report += (
            f"\n### Summary\n"
            f"- **Total Lines**: {total_lines:,}\n"
            f"- **Total Classes**: {total_classes}\n"
            f"- **Total Functions**: {total_funcs}\n"
            f"- **Average lines/file**: {total_lines // max(len(py_files), 1)}\n"
        )

        if issues:
            report += f"\n### Issues Found ({len(issues)})\n\n"
            for issue in issues[:20]:
                report += f"- {issue}\n"
            if len(issues) > 20:
                report += f"\n... and {len(issues) - 20} more\n"

        return {"status": "ok", "skill": "code-reviewer", "response": report,
                "data": {"files": len(py_files), "total_lines": total_lines, "issues": len(issues)}}

    def _review_single_file(self, path: Path) -> dict:
        content = path.read_text(errors="ignore")
        lines = content.splitlines()
        funcs = [(i, l.strip()) for i, l in enumerate(lines, 1) if l.strip().startswith("def ")]
        classes = [(i, l.strip()) for i, l in enumerate(lines, 1) if l.strip().startswith("class ")]

        report = f"## Code Review: {path.name}\n\n"
        report += f"- **Lines**: {len(lines):,}\n"
        report += f"- **Classes**: {len(classes)}\n"
        report += f"- **Functions**: {len(funcs)}\n\n"

        if classes:
            report += "### Classes\n"
            for line_no, cls in classes:
                report += f"- L{line_no}: `{cls}`\n"
            report += "\n"

        if funcs:
            report += "### Functions\n"
            for line_no, fn in funcs[:30]:
                report += f"- L{line_no}: `{fn}`\n"
            if len(funcs) > 30:
                report += f"- ... and {len(funcs) - 30} more\n"

        return {"status": "ok", "skill": "code-reviewer", "response": report}

    # ── Skill 4: Project Planner ──────────────────────────────

    def skill_project_planner(self, user_message: str, **kwargs) -> dict:
        """Break down a requirement into structured project plan."""
        msg = user_message.strip()
        lang = "zh" if any('\u4e00' <= c <= '\u9fff' for c in msg) else "en"

        # Extract key topics
        topics = re.split(r'[，。！？、；：\s,.!?;:]+', msg)
        topics = [t for t in topics if len(t) > 1][:8]
        topic_str = "、".join(topics[:3]) if topics else msg[:50]

        if lang == "zh":
            report = (
                f"## 项目规划：{topic_str}\n\n"
                f"### 阶段一：发现（Discovery）— 1-2 周\n"
                f"**目标**：明确需求边界和成功标准\n\n"
                f"| 任务 | 负责角色 | 优先级 | 预计工时 |\n"
                f"|------|---------|--------|--------|\n"
                f"| 需求调研和用户访谈 | Researcher | P0 | 3天 |\n"
                f"| 竞品分析 | Analyst | P0 | 2天 |\n"
                f"| 技术可行性评估 | Chief Architect | P1 | 2天 |\n"
                f"| 风险预评估 | Risk Auditor | P1 | 1天 |\n\n"
                f"### 阶段二：设计（Design）— 2-3 周\n"
                f"**目标**：产出技术方案和原型\n\n"
                f"| 任务 | 负责角色 | 优先级 | 预计工时 |\n"
                f"|------|---------|--------|--------|\n"
                f"| 系统架构设计 | Chief Architect | P0 | 5天 |\n"
                f"| 用户体验设计 | UX Lead | P0 | 5天 |\n"
                f"| 数据模型设计 | Analyst | P1 | 3天 |\n"
                f"| 方案评审 | Spec Family | P0 | 1天 |\n\n"
                f"### 阶段三：构建（Build）— 3-4 周\n"
                f"**目标**：MVP 开发和集成\n\n"
                f"| 任务 | 负责角色 | 优先级 | 预计工时 |\n"
                f"|------|---------|--------|--------|\n"
                f"| 核心功能开发 | Creator | P0 | 10天 |\n"
                f"| 接口集成 | Chief Architect | P0 | 5天 |\n"
                f"| 内容/文档制作 | Creator | P1 | 3天 |\n"
                f"| 持续测试 | QA (Spec) | P0 | 持续 |\n\n"
                f"### 阶段四：验证（Validate）— 1-2 周\n"
                f"**目标**：质量保证和用户验收\n\n"
                f"| 任务 | 负责角色 | 优先级 | 预计工时 |\n"
                f"|------|---------|--------|--------|\n"
                f"| 端到端测试 | QA Director | P0 | 3天 |\n"
                f"| 安全审计 | Risk Auditor | P0 | 2天 |\n"
                f"| 用户验收测试 | UX Lead | P0 | 2天 |\n"
                f"| 性能优化 | Chief Architect | P1 | 2天 |\n\n"
                f"### 阶段五：交付（Deliver）— 1 周\n"
                f"**目标**：上线和知识沉淀\n\n"
                f"| 任务 | 负责角色 | 优先级 | 预计工时 |\n"
                f"|------|---------|--------|--------|\n"
                f"| 部署上线 | Chief Architect | P0 | 2天 |\n"
                f"| 文档发布 | Creator | P0 | 2天 |\n"
                f"| 复盘总结 | Trum Family | P1 | 1天 |\n"
                f"| 知识沉淀 | Researcher | P1 | 1天 |\n\n"
                f"---\n"
                f"**总工期**：8-12 周 | **关键路径**：发现→架构设计→核心开发→测试\n"
                f"**Ghost Channel**：全程加密通信 + 审计追踪\n"
            )
        else:
            report = (
                f"## Project Plan: {topic_str}\n\n"
                f"### Phase 1: Discovery — 1-2 weeks\n"
                f"**Goal**: Define scope and success criteria\n\n"
                f"| Task | Owner | Priority | Estimate |\n"
                f"|------|-------|----------|----------|\n"
                f"| Requirements research | Researcher | P0 | 3d |\n"
                f"| Competitive analysis | Analyst | P0 | 2d |\n"
                f"| Technical feasibility | Chief Architect | P1 | 2d |\n"
                f"| Risk pre-assessment | Risk Auditor | P1 | 1d |\n\n"
                f"### Phase 2: Design — 2-3 weeks\n"
                f"**Goal**: Technical design and prototyping\n\n"
                f"| Task | Owner | Priority | Estimate |\n"
                f"|------|-------|----------|----------|\n"
                f"| System architecture | Chief Architect | P0 | 5d |\n"
                f"| UX design | UX Lead | P0 | 5d |\n"
                f"| Data modeling | Analyst | P1 | 3d |\n"
                f"| Design review | Spec Family | P0 | 1d |\n\n"
                f"### Phase 3: Build — 3-4 weeks\n"
                f"**Goal**: MVP development\n\n"
                f"| Task | Owner | Priority | Estimate |\n"
                f"|------|-------|----------|----------|\n"
                f"| Core development | Creator | P0 | 10d |\n"
                f"| Integration | Chief Architect | P0 | 5d |\n"
                f"| Documentation | Creator | P1 | 3d |\n"
                f"| Continuous testing | QA (Spec) | P0 | ongoing |\n\n"
                f"### Phase 4: Validate — 1-2 weeks\n"
                f"**Goal**: Quality assurance\n\n"
                f"| Task | Owner | Priority | Estimate |\n"
                f"|------|-------|----------|----------|\n"
                f"| E2E testing | QA Director | P0 | 3d |\n"
                f"| Security audit | Risk Auditor | P0 | 2d |\n"
                f"| UAT | UX Lead | P0 | 2d |\n"
                f"| Performance tuning | Chief Architect | P1 | 2d |\n\n"
                f"### Phase 5: Deliver — 1 week\n\n"
                f"| Task | Owner | Priority | Estimate |\n"
                f"|------|-------|----------|----------|\n"
                f"| Deployment | Chief Architect | P0 | 2d |\n"
                f"| Documentation release | Creator | P0 | 2d |\n"
                f"| Retrospective | Trum Family | P1 | 1d |\n"
                f"| Knowledge capture | Researcher | P1 | 1d |\n\n"
                f"---\n"
                f"**Timeline**: 8-12 weeks | **Critical Path**: Discovery → Architecture → Core Dev → Testing\n"
            )

        return {"status": "ok", "skill": "project-planner", "response": report,
                "data": {"phases": 5, "estimated_weeks": "8-12"}}

    # ── Skill 5: System Reporter ──────────────────────────────

    def skill_system_reporter(self, user_message: str, **kwargs) -> dict:
        """Generate a comprehensive system status report from the database."""
        db_path = self.db_path or self._find_db()
        if not db_path:
            return {"status": "error", "error": "Database not found"}

        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        except Exception:
            try:
                import tempfile
                fallback = Path(tempfile.gettempdir()) / "qspectrum_data" / "platform.db"
                if fallback.exists():
                    conn = sqlite3.connect(str(fallback), timeout=10, check_same_thread=False)
                else:
                    return {"status": "error", "error": "Cannot connect to database"}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        try:
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            table_names = [t[0] for t in tables]

            # Table statistics
            table_stats = []
            total_rows = 0
            for name in table_names:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()[0]
                    total_rows += count
                    table_stats.append((name, count))
                except Exception:
                    table_stats.append((name, -1))

            # Key entities
            roles = conn.execute("SELECT role_code, role_name, family FROM ai_roles ORDER BY role_code").fetchall()
            workflows = conn.execute("SELECT workflow_name, description FROM workflow_definitions").fetchall()
            projects = conn.execute("SELECT project_name, status FROM projects").fetchall()
            docs = conn.execute("SELECT title FROM documents LIMIT 10").fetchall()

            report = (
                f"## Q-SpecTrum System Status Report\n"
                f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                f"### Database Overview\n"
                f"- **Tables**: {len(table_names)}\n"
                f"- **Total Rows**: {total_rows:,}\n"
                f"- **Empty Tables**: {sum(1 for _, c in table_stats if c == 0)}\n\n"
            )

            # Domain grouping
            domains = {
                "Roles & Permissions": [t for t in table_stats if any(k in t[0] for k in ["role", "permission", "family"])],
                "Workflows": [t for t in table_stats if any(k in t[0] for k in ["workflow", "step"])],
                "Projects": [t for t in table_stats if "project" in t[0]],
                "Knowledge": [t for t in table_stats if any(k in t[0] for k in ["knowledge", "document", "skill"])],
                "Communication": [t for t in table_stats if any(k in t[0] for k in ["interaction", "collaboration", "message"])],
                "Ghost Channel": [t for t in table_stats if "ghost" in t[0].lower() or "gc_" in t[0].lower()],
            }

            report += "### Domain Coverage\n\n"
            for domain, tables in domains.items():
                if tables:
                    rows = sum(c for _, c in tables if c >= 0)
                    report += f"**{domain}**: {len(tables)} tables, {rows} rows\n"

            report += f"\n### AI Roles ({len(roles)})\n\n"
            for code, name, family in roles:
                report += f"- `{code}` {name} [{family}]\n"

            report += f"\n### Workflows ({len(workflows)})\n\n"
            for name, desc in workflows:
                report += f"- **{name}**: {(desc or '')[:60]}\n"

            report += f"\n### Projects ({len(projects)})\n\n"
            for name, status in projects:
                report += f"- {name} [{status}]\n"

            conn.close()

            return {"status": "ok", "skill": "system-reporter", "response": report,
                    "data": {"tables": len(table_names), "total_rows": total_rows, "roles": len(roles)}}

        except Exception as e:
            conn.close()
            return {"status": "error", "error": str(e)}

    def _find_db(self) -> str:
        """Find the platform.db file."""
        import tempfile
        candidates = [
            self.project_root / "AI项目管理" / "Platform" / "databases" / "platform.db",
            self.project_root / "platform.db",
            Path(tempfile.gettempdir()) / "qspectrum_data" / "platform.db",
        ]
        for c in candidates:
            if c.exists():
                return str(c)
        return None
