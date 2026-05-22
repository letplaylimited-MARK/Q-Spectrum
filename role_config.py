"""
Q-SpecTrum YAML Pluggable Role Configuration v1.0
===================================================
Implements Point #15: New roles via YAML without code changes.

Users can create custom roles by placing YAML files in:
  - roles/custom/*.yaml     (project-level custom roles)
  - roles/templates/*.yaml  (shared role templates)

YAML Role Schema:
  role_code: ROLE-C01
  role_name: Custom Analyst
  family: qcm
  priority: P2
  description: A custom analytics role
  capabilities:
    - data_analysis
    - report_generation
  system_prompt: |
    You are a custom analyst specializing in...
  triggers:
    keywords: [分析, 数据, analyze, data]
    patterns: ["数据.*分析", "analyze.*data"]
  constraints:
    max_tokens: 2000
    require_gc: false
    min_tier: trial
  metadata:
    author: user
    version: "1.0"
    tags: [analytics, custom]
"""

import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("q-spectrum.role-config")

# Use PyYAML if available, fall back to a simple parser
try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


# ═══════════════════════════════════════════════════════════
# 1. SIMPLE YAML PARSER (fallback when PyYAML not installed)
# ═══════════════════════════════════════════════════════════

def _simple_yaml_parse(text: str) -> dict:
    """
    Minimal YAML-subset parser for role configs.
    Handles: scalars, lists (- item), nested maps (indentation).
    Does NOT handle: anchors, aliases, flow collections, multi-doc.
    """
    result = {}
    stack = [(result, -1)]  # (current_dict, indent_level)
    current_key = None
    collecting_block = False
    block_key = None
    block_indent = 0
    block_lines = []

    for line in text.split("\n"):
        stripped = line.strip()

        # Skip comments and empty lines (unless in block scalar)
        if not stripped or stripped.startswith("#"):
            if collecting_block:
                block_lines.append("")
            continue

        indent = len(line) - len(line.lstrip())

        # Block scalar collection
        if collecting_block:
            if indent > block_indent or (indent == block_indent and not stripped.endswith(":")):
                block_lines.append(line[block_indent:] if len(line) > block_indent else stripped)
                continue
            else:
                # End block scalar
                target = stack[-1][0]
                target[block_key] = "\n".join(block_lines).rstrip()
                collecting_block = False
                block_lines = []

        # List item
        if stripped.startswith("- "):
            item = stripped[2:].strip()
            # Remove quotes
            if (item.startswith('"') and item.endswith('"')) or \
               (item.startswith("'") and item.endswith("'")):
                item = item[1:-1]
            target = stack[-1][0]
            if current_key and current_key in target:
                if isinstance(target[current_key], list):
                    target[current_key].append(item)
            elif current_key:
                target[current_key] = [item]
            continue

        # Key: value
        if ":" in stripped:
            # Pop stack to find correct parent
            while len(stack) > 1 and stack[-1][1] >= indent:
                stack.pop()

            colon_pos = stripped.index(":")
            key = stripped[:colon_pos].strip()
            value = stripped[colon_pos + 1:].strip()

            target = stack[-1][0]

            if value == "|" or value == ">":
                # Block scalar
                collecting_block = True
                block_key = key
                block_indent = indent + 2
                block_lines = []
                current_key = key
                continue

            if value == "":
                # Nested mapping or list start
                target[key] = {}
                stack.append((target[key], indent))
                current_key = key
            elif value.startswith("[") and value.endswith("]"):
                # Inline list
                items = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
                target[key] = items
                current_key = key
            else:
                # Scalar value
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                elif value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value.isdigit():
                    value = int(value)
                else:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                target[key] = value
                current_key = key

    # Flush any remaining block scalar
    if collecting_block and block_key:
        target = stack[-1][0]
        target[block_key] = "\n".join(block_lines).rstrip()

    return result


def parse_yaml(text: str) -> dict:
    """Parse YAML using PyYAML if available, otherwise fallback parser."""
    if _HAS_YAML:
        return yaml.safe_load(text) or {}
    return _simple_yaml_parse(text)


# ═══════════════════════════════════════════════════════════
# 2. ROLE CONFIG MODEL
# ═══════════════════════════════════════════════════════════

@dataclass
class RoleConfig:
    """A role definition loaded from YAML."""
    role_code: str
    role_name: str
    family: str = "qcm"
    priority: str = "P2"
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    system_prompt: str = ""
    trigger_keywords: List[str] = field(default_factory=list)
    trigger_patterns: List[str] = field(default_factory=list)
    max_tokens: int = 2000
    require_gc: bool = False
    min_tier: str = "trial"
    author: str = "user"
    version: str = "1.0"
    tags: List[str] = field(default_factory=list)
    source_file: str = ""
    loaded_at: float = 0.0

    def to_db_dict(self) -> dict:
        """Convert to format compatible with QSpectrumDB role storage."""
        return {
            "role_code": self.role_code,
            "role_name": self.role_name,
            "family": self.family,
            "priority": self.priority,
            "system_prompt": self.system_prompt or f"You are {self.role_name}. {self.description}",
            "capabilities_list": self.capabilities,
            "source": "yaml",
            "source_file": self.source_file,
        }

    def matches_input(self, user_input: str) -> float:
        """Score how well this role matches user input (0-1)."""
        text = user_input.lower()
        score = 0.0

        # Keyword matching
        if self.trigger_keywords:
            matches = sum(1 for kw in self.trigger_keywords if kw.lower() in text)
            score += (matches / len(self.trigger_keywords)) * 0.6

        # Pattern matching
        if self.trigger_patterns:
            pattern_hits = sum(
                1 for pat in self.trigger_patterns
                if re.search(pat, text, re.IGNORECASE)
            )
            score += (pattern_hits / len(self.trigger_patterns)) * 0.4

        return min(1.0, score)


# ═══════════════════════════════════════════════════════════
# 3. YAML ROLE LOADER
# ═══════════════════════════════════════════════════════════

class YAMLRoleLoader:
    """
    Load and manage YAML-defined roles.

    Scans directories for .yaml/.yml files, parses them into
    RoleConfig objects, and registers them with the engine.
    """

    def __init__(self, base_dir: str = None):
        self._base_dir = Path(base_dir or Path(__file__).parent)
        self._roles: Dict[str, RoleConfig] = {}
        self._load_errors: List[dict] = []
        self._scan_dirs = [
            self._base_dir / "roles" / "custom",
            self._base_dir / "roles" / "templates",
            self._base_dir / "AI项目管理" / "Platform" / "roles",
        ]

    def scan_and_load(self) -> Dict[str, RoleConfig]:
        """Scan all configured directories for YAML role files."""
        self._roles.clear()
        self._load_errors.clear()

        for scan_dir in self._scan_dirs:
            if not scan_dir.exists():
                continue
            for yaml_file in scan_dir.glob("**/*.y*ml"):
                if yaml_file.suffix not in (".yaml", ".yml"):
                    continue
                try:
                    self._load_file(yaml_file)
                except Exception as e:
                    self._load_errors.append({
                        "file": str(yaml_file),
                        "error": str(e),
                        "time": time.time(),
                    })
                    logger.warning(f"Failed to load role YAML: {yaml_file}: {e}")

        logger.info(f"Loaded {len(self._roles)} YAML roles ({len(self._load_errors)} errors)")
        return self._roles

    def _load_file(self, filepath: Path):
        """Load a single YAML role file."""
        text = filepath.read_text(encoding="utf-8")
        data = parse_yaml(text)
        if not data:
            return

        # Support both single role and multi-role files
        if "role_code" in data:
            self._parse_role(data, str(filepath))
        elif "roles" in data and isinstance(data["roles"], (list, dict)):
            roles = data["roles"]
            if isinstance(roles, list):
                for r in roles:
                    if isinstance(r, dict):
                        self._parse_role(r, str(filepath))
            elif isinstance(roles, dict):
                for code, r in roles.items():
                    if isinstance(r, dict):
                        r.setdefault("role_code", code)
                        self._parse_role(r, str(filepath))

    def _parse_role(self, data: dict, source_file: str):
        """Parse a role dict into RoleConfig."""
        code = data.get("role_code", "").strip()
        name = data.get("role_name", "").strip()
        if not code or not name:
            return

        triggers = data.get("triggers", {})
        constraints = data.get("constraints", {})
        metadata = data.get("metadata", {})

        role = RoleConfig(
            role_code=code,
            role_name=name,
            family=data.get("family", "qcm").lower(),
            priority=data.get("priority", "P2"),
            description=data.get("description", ""),
            capabilities=data.get("capabilities", []),
            system_prompt=data.get("system_prompt", ""),
            trigger_keywords=triggers.get("keywords", []) if isinstance(triggers, dict) else [],
            trigger_patterns=triggers.get("patterns", []) if isinstance(triggers, dict) else [],
            max_tokens=constraints.get("max_tokens", 2000) if isinstance(constraints, dict) else 2000,
            require_gc=constraints.get("require_gc", False) if isinstance(constraints, dict) else False,
            min_tier=constraints.get("min_tier", "trial") if isinstance(constraints, dict) else "trial",
            author=metadata.get("author", "user") if isinstance(metadata, dict) else "user",
            version=str(metadata.get("version", "1.0")) if isinstance(metadata, dict) else "1.0",
            tags=metadata.get("tags", []) if isinstance(metadata, dict) else [],
            source_file=source_file,
            loaded_at=time.time(),
        )

        self._roles[code] = role

    def load_from_string(self, yaml_text: str, source: str = "inline") -> Optional[RoleConfig]:
        """Load a single role from a YAML string."""
        data = parse_yaml(yaml_text)
        if data and "role_code" in data:
            self._parse_role(data, source)
            return self._roles.get(data["role_code"])
        return None

    def get_role(self, role_code: str) -> Optional[RoleConfig]:
        return self._roles.get(role_code)

    def list_roles(self) -> List[dict]:
        return [
            {
                "role_code": r.role_code,
                "role_name": r.role_name,
                "family": r.family,
                "description": r.description,
                "capabilities": r.capabilities,
                "tags": r.tags,
                "source": r.source_file,
                "version": r.version,
            }
            for r in self._roles.values()
        ]

    def find_matching_roles(self, user_input: str, threshold: float = 0.2) -> List[Tuple[str, float]]:
        """Find YAML roles that match user input, sorted by score."""
        matches = []
        for code, role in self._roles.items():
            score = role.matches_input(user_input)
            if score >= threshold:
                matches.append((code, score))
        return sorted(matches, key=lambda x: x[1], reverse=True)

    def get_status(self) -> dict:
        families = {}
        for r in self._roles.values():
            families[r.family] = families.get(r.family, 0) + 1
        return {
            "loaded_roles": len(self._roles),
            "families": families,
            "scan_dirs": [str(d) for d in self._scan_dirs if d.exists()],
            "load_errors": len(self._load_errors),
            "errors": self._load_errors[-5:],
        }

    @property
    def roles(self) -> Dict[str, RoleConfig]:
        return self._roles


# ═══════════════════════════════════════════════════════════
# 4. TEMPLATE GENERATOR
# ═══════════════════════════════════════════════════════════

def generate_role_template(role_code: str = "ROLE-C01",
                           role_name: str = "Custom Role",
                           family: str = "qcm") -> str:
    """Generate a YAML template for a new custom role."""
    return f"""# Q-SpecTrum Custom Role Definition
# Place this file in roles/custom/ to auto-load

role_code: {role_code}
role_name: {role_name}
family: {family}
priority: P2
description: A custom {role_name.lower()} role for specialized tasks

capabilities:
  - custom_analysis
  - report_generation

system_prompt: |
  You are {role_name}, a specialized AI role in the Q-SpecTrum system.
  Family: {family.upper()} | Priority: P2

  Your responsibilities:
  1. Analyze user requests related to your specialty
  2. Provide detailed, actionable insights
  3. Coordinate with other roles when needed

  Always maintain professional quality and cite your reasoning.

triggers:
  keywords: [custom, analyze, report]
  patterns: ["custom.*analysis", "generate.*report"]

constraints:
  max_tokens: 2000
  require_gc: false
  min_tier: trial

metadata:
  author: user
  version: "1.0"
  tags: [custom, {family}]
"""


# ═══════════════════════════════════════════════════════════
# 5. SELF-TEST
# ═══════════════════════════════════════════════════════════

def _self_test():
    """Verify YAML role configuration works correctly."""
    import shutil
    import tempfile

    print("=" * 60)
    print("YAML Role Configuration — Self Test")
    print("=" * 60)

    # 1. Test YAML parser
    test_yaml = """
role_code: ROLE-C01
role_name: Social Media Analyst
family: qcm
priority: P2
description: Analyzes social media trends and engagement
capabilities:
  - social_analysis
  - trend_tracking
  - content_strategy
system_prompt: |
  You are a Social Media Analyst.
  Analyze trends and provide strategic insights.
triggers:
  keywords: [社交媒体, social media, 趋势, trend, engagement]
  patterns: ["社交.*分析", "social.*analys"]
constraints:
  max_tokens: 2000
  require_gc: false
  min_tier: trial
metadata:
  author: test
  version: "1.0"
  tags: [social, marketing]
"""
    data = parse_yaml(test_yaml)
    assert data["role_code"] == "ROLE-C01"
    assert "Social Media Analyst" in data["role_name"]
    assert len(data["capabilities"]) == 3
    assert "social_analysis" in data["capabilities"]
    print("  [1] YAML parsing ✅")

    # 2. Test loader
    tmp = tempfile.mkdtemp()
    custom_dir = Path(tmp) / "roles" / "custom"
    custom_dir.mkdir(parents=True)

    # Write test role files
    (custom_dir / "social_analyst.yaml").write_text(test_yaml)
    (custom_dir / "content_writer.yaml").write_text("""
role_code: ROLE-C02
role_name: Content Writer
family: qcm
description: Creates compelling content
capabilities:
  - copywriting
  - blog_posts
triggers:
  keywords: [写作, 文案, write, content, blog]
metadata:
  version: "1.0"
""")

    loader = YAMLRoleLoader(base_dir=tmp)
    roles = loader.scan_and_load()
    assert len(roles) == 2, f"Expected 2 roles, got {len(roles)}"
    assert "ROLE-C01" in roles
    assert "ROLE-C02" in roles
    print(f"  [2] File loading: {len(roles)} roles ✅")

    # 3. Test matching
    r1 = roles["ROLE-C01"]
    assert r1.matches_input("分析社交媒体趋势") > 0.2
    assert r1.matches_input("random unrelated text") < 0.1
    print("  [3] Trigger matching ✅")

    # 4. Test find_matching_roles
    matches = loader.find_matching_roles("帮我写一篇blog文案")
    assert len(matches) > 0
    assert matches[0][0] == "ROLE-C02"  # Content writer should match best
    print(f"  [4] Role matching: top match = {matches[0][0]} (score={matches[0][1]:.2f}) ✅")

    # 5. Test DB format
    db_dict = r1.to_db_dict()
    assert db_dict["role_code"] == "ROLE-C01"
    assert db_dict["source"] == "yaml"
    assert len(db_dict["capabilities_list"]) == 3
    print("  [5] DB format conversion ✅")

    # 6. Test template generation
    template = generate_role_template("ROLE-C99", "Test Role", "spec")
    data2 = parse_yaml(template)
    assert data2["role_code"] == "ROLE-C99"
    assert data2["family"] == "spec"
    print("  [6] Template generation ✅")

    # 7. Test load_from_string
    inline = loader.load_from_string("""
role_code: ROLE-C03
role_name: Inline Test
family: trum
capabilities:
  - testing
triggers:
  keywords: [test, inline]
""")
    assert inline is not None
    assert inline.family == "trum"
    print("  [7] Inline loading ✅")

    # 8. Test status
    status = loader.get_status()
    assert status["loaded_roles"] == 3
    print(f"  [8] Status: {status['loaded_roles']} roles, families={status['families']} ✅")

    shutil.rmtree(tmp, ignore_errors=True)

    print("=" * 60)
    print("ALL TESTS PASSED ✅")
    print("=" * 60)
    return True


if __name__ == "__main__":
    _self_test()
