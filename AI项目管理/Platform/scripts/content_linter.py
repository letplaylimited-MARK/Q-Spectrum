#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容质量检查器 V2 (Content Linter)
守住质量大门：自动检查 Markdown 文档的元数据、结构、链接和质量指标。
支持针对“实战案例”的差异化检查规则。
"""

import re
import sys
from datetime import datetime
from pathlib import Path

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

# Dynamic path resolution: locate parent directory of the AI项目管理 folder
ROOT = Path(__file__).parent.parent.parent

# 定义不同类型文档的检查规则
RULES = {
    "topic": {
        "required_sections": ["简介", "为什么重要"],
        "min_words": 500,
        "quality_indicators": ["学习路径", "决策矩阵", "正误对比", "实战案例"],
        "section_mapping": {
            "核心内容": ["协作过程全记录", "核心内容", "核心内容"],
            "常见问题": ["经验教训", "常见问题", "FAQ"],
            "多维度评估": ["多维度评估", "综合评分", "评估"],
            "相关链接": ["相关链接", "关联记录", "链接"],
        },
    },
    "skill": {
        "required_sections": [
            "激活词",
            "使用时机",
            "核心工作流",
            "交付物",
            "验证方法",
            "关联技能",
        ],
        "min_words": 300,
        "quality_indicators": ["常见错误", "学习路径", "多维度评估"],
    },
    "resource": {
        "required_sections": [
            "简介",
            "为什么值得记录",
            "推荐使用方式",
            "与知识库的关系",
        ],
        "min_words": 200,
        "quality_indicators": ["7 维度评估", "学习路径", "适用阶段"],
    },
    "template": {
        "required_sections": ["用途", "使用方法"],
        "min_words": 100,
        "quality_indicators": [],
    },
    "faq": {"required_sections": [], "min_words": 100, "quality_indicators": []},
    "weekly": {
        "required_sections": ["复盘", "整理", "计划"],
        "min_words": 300,
        "quality_indicators": ["反哺需求池", "反哺技能机会池", "飞轮记录"],
    },
    "project": {
        "required_sections": ["项目基本信息", "当前系统分层状态", "已完成的推进轮次"],
        "min_words": 200,
        "quality_indicators": ["当前薄弱点", "下一阶段重点"],
    },
    "map": {"required_sections": [], "min_words": 100, "quality_indicators": []},
    "demand": {
        "required_sections": ["来源", "建议解法"],
        "min_words": 150,
        "quality_indicators": ["验收标准", "关联记录"],
    },
    "pain": {
        "required_sections": ["痛点描述", "根因分析"],
        "min_words": 150,
        "quality_indicators": ["解决方案"],
    },
    "defect": {
        "required_sections": ["缺陷信息", "问题描述", "修复方案"],
        "min_words": 150,
        "quality_indicators": ["验证结果"],
    },
    "validation": {
        "required_sections": ["验证目标", "验证检查项"],
        "min_words": 150,
        "quality_indicators": ["验证结论"],
    },
    "handoff": {"required_sections": [], "min_words": 100, "quality_indicators": []},
}


class LintResult:
    def __init__(self, file_path):
        self.file = file_path
        self.errors = []
        self.warnings = []
        self.score = 100

    def add_error(self, msg):
        self.errors.append(msg)
        self.score -= 20

    def add_warning(self, msg):
        self.warnings.append(msg)
        self.score -= 5

    @property
    def status(self):
        if self.score >= 90:
            return "✅ PASS"
        if self.score >= 70:
            return "⚠️  WARN"
        return "❌ FAIL"


def parse_yaml_front_matter(content):
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    yaml_text = match.group(1)
    metadata = {}
    for line in yaml_text.split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            metadata[key.strip()] = val.strip()
    return metadata


def check_file(file_path: Path) -> LintResult:
    result = LintResult(file_path)
    content = file_path.read_text(encoding="utf-8")

    # 1. Metadata Check
    meta = parse_yaml_front_matter(content)
    if not meta:
        result.add_error("缺失 YAML 元数据头部")
    else:
        for key in ["entity_type", "entity_code", "title"]:
            if key not in meta:
                result.add_error(f"元数据缺失必填字段: {key}")

    entity_type = meta.get("entity_type", "").lower()
    rules = RULES.get(entity_type, {})

    # 2. Structure Check
    headings = re.findall(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)

    # Check required sections
    for section in rules.get("required_sections", []):
        if not any(section in h for h in headings):
            result.add_error(f"缺失关键章节: {section}")

    # Check mapped sections (for flexible naming like Case Studies)
    if "topic" in entity_type and "section_mapping" in rules:
        for standard_name, alternatives in rules["section_mapping"].items():
            found = False
            for alt in alternatives:
                if any(alt in h for h in headings):
                    found = True
                    break
            if not found:
                result.add_error(
                    f"缺失关键章节: {standard_name} (或: {', '.join(alternatives)})"
                )

    # 3. Word Count Check
    word_count = len(re.findall(r"[\u4e00-\u9fa5a-zA-Z0-9]", content))
    min_words = rules.get("min_words", 100)
    if word_count < min_words:
        result.add_warning(f"内容过短 ({word_count} 字)，建议 > {min_words} 字")

    # 4. Quality Indicators
    quality_hits = 0
    for indicator in rules.get("quality_indicators", []):
        if indicator in content:
            quality_hits += 1
    if quality_hits == 0 and rules.get("quality_indicators"):
        result.add_warning("未检测到任何质量增强指标 (如：学习路径/实战案例/评估)")

    return result


def run_linter(target_path=None):
    print("=" * 70)
    print("🔍 内容质量检查器 V2 (Content Linter)")
    print(f"⏰ 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    files_to_scan = []

    if target_path:
        # Check specific file
        p = Path(target_path)
        if p.exists():
            files_to_scan.append(p)
        else:
            print(f"❌ 文件不存在: {target_path}")
            return
    else:
        # Check all directories
        dirs_to_scan = [
            ("Topics", "topic"),
            ("Skills", "skill"),
            ("Resources", "resource"),
            ("Templates", "template"),
            ("Maps", "map"),
            ("FAQs", "faq"),
            ("Projects", "project"),
            ("Weekly-Logs", "weekly"),
            ("Operations/Demands", "demand"),
            ("Operations/Pain-Points", "pain"),
            ("Operations/Defects", "defect"),
            ("Operations/Validations", "validation"),
        ]
        for dir_name, expected_type in dirs_to_scan:
            dir_path = ROOT / dir_name
            if dir_path.exists():
                for md_file in sorted(dir_path.glob("*.md")):
                    files_to_scan.append(md_file)

    total_files = 0
    pass_count = 0
    warn_count = 0
    fail_count = 0

    for md_file in files_to_scan:
        total_files += 1
        result = check_file(md_file)

        if "PASS" in result.status:
            pass_count += 1
        elif "WARN" in result.status:
            warn_count += 1
        else:
            fail_count += 1

        # Print details for failures and warnings
        if "PASS" not in result.status:
            print(f"\n{result.status} {md_file.relative_to(ROOT)}")
            for e in result.errors:
                print(f"  ❌ {e}")
            for w in result.warnings:
                print(f"  ⚠️  {w}")

    print("\n" + "=" * 70)
    print("📊 检查汇总")
    print(f"   文件总数: {total_files}")
    print(f"   ✅ 通过: {pass_count}")
    print(f"   ⚠️  警告: {warn_count}")
    print(f"   ❌ 失败: {fail_count}")

    if fail_count > 0:
        print("\n❌ 质量检查未通过，请修复失败的文件。")
    else:
        print("\n✅ 质量检查通过！系统内容健康。")
    print("=" * 70)


if __name__ == "__main__":
    run_linter()
