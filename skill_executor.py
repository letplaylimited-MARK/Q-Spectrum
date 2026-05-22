"""
Q-SpecTrum Lightweight Skill Executor
======================================
Executes DeerFlow skills and Q-SpecTrum skills WITHOUT needing LangGraph.

Key insight: DeerFlow skills are pure prompt instruction templates (SKILL.md).
This executor loads them and feeds them to Q-SpecTrum's LLM provider (Mock or Real).

Architecture:
  User Query
    ↓
  QSpectrumEngine.process()  →  routing + DeerFlow recommendation
    ↓
  SkillExecutor.execute()    →  loads SKILL.md as system prompt
    ↓
  LLM Provider              →  generates structured response per skill instructions
    ↓
  Formatted Result

Skill Sources:
  1. AI项目管理/Skills/  →  16 skill files (12 invocable + 4 reference)
  2. AI项目管理/Skills/                →  16 project management skills
  3. AI项目管理/Systems/ai-skill-system/repos/  →  8 framework skills

Usage:
  from skill_executor import SkillExecutor
  executor = SkillExecutor()
  executor.list_skills()
  result = executor.execute("deep-research", "研究AI項目管理最佳實踐")

CLI:
  python skill_executor.py --list
  python skill_executor.py --run deep-research "研究AI項目管理最佳實踐"
  python skill_executor.py --run 全库盘点 "執行系統盤點"
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional


class SkillExecutor:
    """Lightweight executor: loads SKILL.md → system prompt → LLM → result."""

    def __init__(self, root_dir: Optional[str] = None):
        self.root = Path(root_dir) if root_dir else Path(__file__).parent
        self._skill_cache = {}
        self._discovered = False
        # NOTE: _discover_skills() is now lazy - called on first access to avoid
        # blocking startup on mounted filesystems with slow rglob() operations.

    def _ensure_discovered(self):
        """Lazy discovery trigger - only scan filesystem when actually needed."""
        if not self._discovered:
            self._discover_skills()
            self._discovered = True

    def _discover_skills(self):
        """Discover all available skills from three sources. (Lazy-loaded)"""
        # Source 1: DeerFlow built-in skills
        df_skills = self.root / "DeerFlow" / "DeerFlow" / "skills" / "public"
        if df_skills.exists():
            for skill_dir in sorted(df_skills.iterdir()):
                if skill_dir.is_dir():
                    manifest = skill_dir / "SKILL.md"
                    if manifest.exists():
                        self._skill_cache[skill_dir.name] = {
                            "name": skill_dir.name,
                            "source": "deerflow",
                            "path": str(manifest),
                            "scripts": list(skill_dir.glob("scripts/*.py")),
                        }

        # Source 2: Q-SpecTrum project skills
        qs_skills = self.root / "AI项目管理" / "Skills"
        if qs_skills.exists():
            for md_file in sorted(qs_skills.glob("*.md")):
                # Use simplified name as key
                name = md_file.stem
                # Extract skill number if present
                short_name = name.lower().replace(" ", "-")
                self._skill_cache[short_name] = {
                    "name": name,
                    "source": "qspectrum",
                    "path": str(md_file),
                    "scripts": [],
                }

        # Source 3: ai-skill-system repos
        repos_dir = self.root / "AI项目管理" / "Systems" / "ai-skill-system" / "repos"
        if repos_dir.exists():
            for repo_dir in sorted(repos_dir.iterdir()):
                if repo_dir.is_dir() and repo_dir.name != "ai-skill-web-app":
                    # Find the main skill manifest
                    manifest = None
                    for candidate in [
                        repo_dir / "SKILL.md",
                        repo_dir / "skill.md",
                    ]:
                        if candidate.exists():
                            manifest = candidate
                            break
                    if not manifest:
                        # Look for system-prompt files
                        for candidate in repo_dir.rglob("system-prompt-full.md"):
                            manifest = candidate
                            break
                    if not manifest:
                        # Use any .md in root
                        mds = list(repo_dir.glob("*.md"))
                        if mds:
                            manifest = mds[0]
                    if manifest:
                        self._skill_cache[f"repo:{repo_dir.name}"] = {
                            "name": repo_dir.name,
                            "source": "ai-skill-system",
                            "path": str(manifest),
                            "scripts": list(repo_dir.rglob("*.py")),
                        }

    def list_skills(self) -> List[Dict]:
        """List all discovered skills."""
        self._ensure_discovered()
        result = []
        for key, info in sorted(self._skill_cache.items()):
            # Read first 200 chars for description
            try:
                text = Path(info["path"]).read_text(encoding="utf-8", errors="ignore")[:500]
                desc = ""
                for line in text.split("\n"):
                    if line.strip().startswith("description:"):
                        desc = line.split(":", 1)[1].strip().strip('"')
                        break
                    if line.startswith("# ") and not desc:
                        desc = line[2:].strip()
                if not desc:
                    desc = info["name"]
            except Exception:
                desc = info["name"]

            result.append({
                "key": key,
                "name": info["name"],
                "source": info["source"],
                "description": desc[:100],
                "has_scripts": len(info["scripts"]) > 0,
            })
        return result

    def load_skill(self, skill_key: str) -> Optional[Dict]:
        """Load a skill's manifest content."""
        self._ensure_discovered()
        # Try exact match
        info = self._skill_cache.get(skill_key)

        # Try fuzzy match
        if not info:
            for key, val in self._skill_cache.items():
                if skill_key.lower() in key.lower() or skill_key.lower() in val["name"].lower():
                    info = val
                    break

        if not info:
            return None

        try:
            content = Path(info["path"]).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

        # Extract frontmatter
        frontmatter = {}
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        frontmatter[k.strip()] = v.strip().strip('"')
                body = parts[2].strip()

        return {
            "key": skill_key,
            "name": info["name"],
            "source": info["source"],
            "frontmatter": frontmatter,
            "body": body,
            "full_content": content,
            "has_scripts": len(info["scripts"]) > 0,
            "script_paths": [str(s) for s in info["scripts"]],
        }

    def execute(self, skill_key: str, user_request: str,
                llm_provider=None, role_context: Optional[Dict] = None,
                force_script: bool = False) -> Dict:
        """
        Execute a skill by loading its SKILL.md and feeding it to the LLM.
        If the skill has executable scripts, tries script execution first.

        Args:
            skill_key: Skill identifier (e.g., "deep-research", "全库盘点")
            user_request: User's actual request
            llm_provider: LLM to use (defaults to engine's MockLLM)
            role_context: Optional role routing context
            force_script: If True, only use script execution (skip LLM fallback)

        Returns:
            {"status": "ok"|"error", "skill": ..., "response": ..., "metadata": ...}
        """
        skill = self.load_skill(skill_key)
        if not skill:
            return {
                "status": "error",
                "error": f"Skill '{skill_key}' not found",
                "available": [s["key"] for s in self.list_skills()[:10]],
            }

        # Try script execution first if available
        if skill["has_scripts"]:
            runner = SkillRunner(project_root=str(self.root))
            if runner.can_run(skill):
                script_result = runner.run(skill_key, user_request, self, str(self.root))
                if script_result["status"] == "ok":
                    return {
                        "status": "ok",
                        "skill": {
                            "key": skill["key"],
                            "name": skill["name"],
                            "source": skill["source"],
                        },
                        "response": script_result.get("output", ""),
                        "metadata": {
                            "execution_method": "script",
                            "script": script_result.get("script"),
                            "duration": script_result.get("duration"),
                            "returncode": script_result.get("returncode"),
                            "has_scripts": skill["has_scripts"],
                        },
                    }
                # If script fails and force_script=True, return error
                if force_script:
                    return {
                        "status": "error",
                        "error": f"Script execution failed: {script_result.get('stderr', 'Unknown error')}",
                        "skill": {
                            "key": skill["key"],
                            "name": skill["name"],
                            "source": skill["source"],
                        },
                        "metadata": {
                            "execution_method": "script",
                            "returncode": script_result.get("returncode"),
                        },
                    }

        # Fall back to LLM execution
        if force_script:
            return {
                "status": "error",
                "error": f"Skill '{skill_key}' has no executable scripts (--execute requires scripts)",
                "skill": {
                    "key": skill["key"],
                    "name": skill["name"],
                    "source": skill["source"],
                },
            }

        # Build system prompt from skill body
        system_prompt = self._build_system_prompt(skill, user_request, role_context)

        # Use provided LLM or create default
        if llm_provider is None:
            from qspectrum_engine import QSpectrumDB, create_llm_provider
            db = QSpectrumDB()
            llm_provider, llm_name = create_llm_provider(db=db)
        else:
            llm_name = type(llm_provider).__name__

        # Generate response
        role_name = role_context.get("role_name", "Skill Executor") if role_context else "Skill Executor"
        role_code = role_context.get("role_code", "SKILL") if role_context else "SKILL"
        family = role_context.get("family", "qcm") if role_context else "qcm"

        response = llm_provider.generate(
            system_prompt=system_prompt,
            user_message=user_request,
            role_name=role_name,
            role_code=role_code,
            family=family,
        )

        return {
            "status": "ok",
            "skill": {
                "key": skill["key"],
                "name": skill["name"],
                "source": skill["source"],
            },
            "response": response,
            "metadata": {
                "execution_method": "llm",
                "llm": llm_name,
                "system_prompt_length": len(system_prompt),
                "has_scripts": skill["has_scripts"],
                "script_note": (
                    f"This skill references {len(skill['script_paths'])} Python scripts "
                    f"that can be executed for full functionality."
                    if skill["has_scripts"] else None
                ),
            },
        }

    def _build_system_prompt(self, skill: Dict, user_request: str,
                             role_context: Optional[Dict] = None) -> str:
        """Build a system prompt by combining skill manifest + Q-SpecTrum context."""
        parts = []

        # Skill identity
        parts.append(f"# You are executing skill: {skill['name']}")
        parts.append(f"Source: {skill['source']}")
        parts.append("")

        # Q-SpecTrum context
        parts.append("## Q-SpecTrum Project Context")
        parts.append("- Platform: AI Project Platform MVP (active)")
        parts.append("- Database: 40 tables, 85 rows, 0 empty tables")
        parts.append("- Roles: 15 AI roles across 3 families (Trum/Spec/QCM)")
        parts.append("- Workflows: 4 (84 steps, Initiation→Planning→Execution→Validation→Delivery)")
        if role_context:
            parts.append(f"- Assigned Role: {role_context.get('role_name', '?')} ({role_context.get('role_code', '?')})")
        parts.append("")

        # Skill instructions (the body of SKILL.md)
        parts.append("## Skill Instructions")
        parts.append("Follow these instructions to complete the task:")
        parts.append("")
        # Truncate very long skills to fit context
        body = skill["body"]
        if len(body) > 3000:
            body = body[:3000] + "\n\n[... truncated for context limit ...]"
        parts.append(body)

        if skill["has_scripts"]:
            parts.append("")
            parts.append("## Available Scripts")
            for sp in skill["script_paths"][:5]:
                parts.append(f"- {sp}")

        return "\n".join(parts)


class SkillRunner:
    """
    Actually executes skill scripts in a sandboxed subprocess.

    Unlike SkillExecutor which feeds SKILL.md to an LLM, SkillRunner
    directly executes the Python scripts referenced by skills, allowing
    for deterministic, repeatable results without LLM generation.
    """

    def __init__(self, project_root: str, timeout: int = 30, max_output: int = 50000):
        """
        Initialize the SkillRunner with sandbox constraints.

        Args:
            project_root: Root directory for project context
            timeout: Maximum execution time in seconds
            max_output: Maximum output length in characters
        """
        self.project_root = project_root
        self.timeout = timeout
        self.max_output = max_output

    def can_run(self, skill_info: Dict) -> bool:
        """
        Check if a skill has executable Python scripts.

        Args:
            skill_info: Skill info dict (from load_skill)

        Returns:
            True if skill has at least one .py script
        """
        return skill_info.get("has_scripts", False) and len(skill_info.get("script_paths", [])) > 0

    def run(self, skill_key: str, user_request: str, skill_executor: 'SkillExecutor',
            project_root: str = None) -> Dict:
        """
        Main execution method: load skill, find script, execute in sandbox.

        Args:
            skill_key: Skill identifier
            user_request: User's request text
            skill_executor: SkillExecutor instance for loading skills
            project_root: Optional project root override

        Returns:
            {
                "status": "ok"|"error",
                "output": <stdout or parsed JSON>,
                "stderr": <stderr output>,
                "returncode": <exit code>,
                "duration": <execution time in seconds>,
                "script": <path to executed script>,
                "method": "script_execution"
            }
        """
        start_time = time.time()
        project_root = project_root or self.project_root

        # Load skill
        skill = skill_executor.load_skill(skill_key)
        if not skill:
            return {
                "status": "error",
                "error": f"Skill '{skill_key}' not found",
                "duration": time.time() - start_time,
            }

        # Find the primary script
        script_path = self._find_primary_script(skill["script_paths"])
        if not script_path:
            return {
                "status": "error",
                "error": f"No executable Python scripts found in skill '{skill_key}'",
                "duration": time.time() - start_time,
            }

        # Create sandbox environment
        sandbox_env = self._create_sandbox_env(skill["name"], user_request, project_root)

        # Create temp working directory
        with tempfile.TemporaryDirectory(prefix=f"skill_{skill_key.replace(':', '_')}_") as tmpdir:
            try:
                # Execute script
                result = subprocess.run(
                    [sys.executable, script_path],
                    cwd=tmpdir,
                    env=sandbox_env,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )

                # Parse output
                stdout = result.stdout[:self.max_output] if result.stdout else ""
                stderr = result.stderr[:self.max_output] if result.stderr else ""

                # Try to parse JSON from output
                parsed_output = self._parse_output(stdout)

                duration = time.time() - start_time
                return {
                    "status": "ok" if result.returncode == 0 else "error",
                    "output": parsed_output,
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": result.returncode,
                    "duration": duration,
                    "script": script_path,
                    "method": "script_execution",
                }

            except subprocess.TimeoutExpired:
                duration = time.time() - start_time
                return {
                    "status": "error",
                    "error": f"Script execution timed out after {self.timeout}s",
                    "duration": duration,
                    "script": script_path,
                    "returncode": -1,
                }

            except Exception as e:
                duration = time.time() - start_time
                return {
                    "status": "error",
                    "error": str(e),
                    "stderr": str(e),
                    "duration": duration,
                    "script": script_path,
                    "returncode": -1,
                }

    def _find_primary_script(self, script_paths: List[str]) -> Optional[str]:
        """
        Find the best script to execute from a list of paths.

        Priority:
        1. main.py
        2. run.py
        3. First .py file in alphabetical order

        Args:
            script_paths: List of script paths (as strings)

        Returns:
            Path to the primary script, or None if none found
        """
        if not script_paths:
            return None

        script_paths = [Path(p) for p in script_paths]

        # Priority 1: main.py
        for sp in script_paths:
            if sp.name == "main.py":
                return str(sp)

        # Priority 2: run.py
        for sp in script_paths:
            if sp.name == "run.py":
                return str(sp)

        # Priority 3: First .py file (sorted)
        py_files = [sp for sp in script_paths if sp.suffix == ".py"]
        if py_files:
            return str(sorted(py_files)[0])

        return None

    def _parse_output(self, stdout: str) -> Dict:
        """
        Try to parse JSON from stdout, fallback to raw text.

        Args:
            stdout: Script's stdout output

        Returns:
            Parsed JSON dict if valid JSON found, else {"raw_output": stdout}
        """
        if not stdout:
            return {"raw_output": ""}

        # Try to find JSON object or array in output
        try:
            # Try direct parse
            return json.loads(stdout)
        except json.JSONDecodeError:
            pass

        # Try to find JSON block (common pattern: "```json ... ```" or just {...})
        lines = stdout.split("\n")
        in_json = False
        json_lines = []

        for line in lines:
            if "```json" in line or "```" in line:
                in_json = not in_json
                continue
            if in_json or line.strip().startswith("{") or line.strip().startswith("["):
                json_lines.append(line)

        if json_lines:
            try:
                return json.loads("\n".join(json_lines))
            except json.JSONDecodeError:
                pass

        # Fallback: return raw output
        return {"raw_output": stdout}

    def _create_sandbox_env(self, skill_name: str, user_request: str,
                            project_root: str) -> Dict[str, str]:
        """
        Build environment variables for sandboxed script execution.

        Args:
            skill_name: Name of the skill being executed
            user_request: User's request text
            project_root: Project root directory

        Returns:
            Dictionary of environment variables
        """
        env = os.environ.copy()

        # Add skill-specific variables
        env["SKILL_INPUT"] = user_request
        env["SKILL_NAME"] = skill_name
        env["PROJECT_ROOT"] = project_root

        # Ensure Python path includes project root
        python_path = env.get("PYTHONPATH", "")
        if project_root not in python_path:
            env["PYTHONPATH"] = f"{project_root}:{python_path}" if python_path else project_root

        # Limit output buffering
        env["PYTHONUNBUFFERED"] = "1"

        return env


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    executor = SkillExecutor()

    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        skills = executor.list_skills()
        print(f"Available Skills ({len(skills)}):\n")
        by_source = {}
        for s in skills:
            by_source.setdefault(s["source"], []).append(s)
        for source, items in sorted(by_source.items()):
            print(f"  [{source}] ({len(items)} skills)")
            for s in items:
                scripts = " [has scripts]" if s["has_scripts"] else ""
                print(f"    {s['key']}: {s['description'][:60]}{scripts}")
            print()

    elif len(sys.argv) > 3 and sys.argv[1] == "--run":
        skill_key = sys.argv[2]
        request = " ".join(sys.argv[3:])
        print(f"Executing skill: {skill_key}")
        print(f"Request: {request}")
        print("-" * 60)
        result = executor.execute(skill_key, request)
        if result["status"] == "ok":
            print(f"Skill: {result['skill']['name']} ({result['skill']['source']})")
            print(f"Execution method: {result['metadata'].get('execution_method', 'unknown')}")
            if result['metadata'].get('execution_method') == 'llm':
                print(f"LLM: {result['metadata']['llm']}")
            else:
                print(f"Script: {result['metadata'].get('script', 'N/A')}")
                print(f"Duration: {result['metadata'].get('duration', 0):.2f}s")
            print()
            print(result["response"])
            if result["metadata"].get("script_note"):
                print(f"\n{result['metadata']['script_note']}")
        else:
            print(f"Error: {result['error']}")

    elif len(sys.argv) > 3 and sys.argv[1] == "--execute":
        skill_key = sys.argv[2]
        request = " ".join(sys.argv[3:])
        print(f"Executing skill (script mode): {skill_key}")
        print(f"Request: {request}")
        print("-" * 60)
        result = executor.execute(skill_key, request, force_script=True)
        if result["status"] == "ok":
            print(f"Skill: {result['skill']['name']} ({result['skill']['source']})")
            print(f"Script: {result['metadata'].get('script', 'N/A')}")
            print(f"Return code: {result['metadata'].get('returncode', 'N/A')}")
            print(f"Duration: {result['metadata'].get('duration', 0):.2f}s")
            print()
            print(result["response"])
        else:
            print(f"Error: {result['error']}")

    elif len(sys.argv) > 2 and sys.argv[1] == "--info":
        skill_key = sys.argv[2]
        skill = executor.load_skill(skill_key)
        if skill:
            print(f"Skill: {skill['name']}")
            print(f"Source: {skill['source']}")
            print(f"Key: {skill['key']}")
            if skill["frontmatter"]:
                print(f"Frontmatter: {json.dumps(skill['frontmatter'], ensure_ascii=False, indent=2)}")
            print(f"Body length: {len(skill['body'])} chars")
            print(f"Scripts: {len(skill['script_paths'])}")
            for sp in skill["script_paths"]:
                print(f"  - {sp}")
        else:
            print(f"Skill '{skill_key}' not found")

    else:
        print("Q-SpecTrum Skill Executor")
        print()
        print("Usage:")
        print("  python skill_executor.py --list                          # List all skills")
        print('  python skill_executor.py --run deep-research "研究AI趨勢"  # Execute (script or LLM)')
        print('  python skill_executor.py --execute deep-research "研究AI趨勢"  # Execute scripts only')
        print("  python skill_executor.py --info deep-research            # Show skill info")
