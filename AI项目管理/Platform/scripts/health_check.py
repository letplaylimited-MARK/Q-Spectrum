#!/usr/bin/env python3
"""
知识库健康度自动分析脚本

功能：
1. 自动扫描所有文档质量
2. 统计元数据覆盖率
3. 检查关联完整性
4. 生成健康度报告
5. 识别需要优化的文档

用法：
    python health_check.py [scan|report|fix]
"""

import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# 设置 UTF-8 输出编码（Windows 需要）
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# 项目根目录
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from path_utils import get_project_root

ROOT = Path(get_project_root())


def extract_title(content: str) -> str:
    """从 Markdown 文档中提取标题"""
    match = re.match(r"^#\s+(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else "Untitled"


# 目录规则映射
DIR_RULES = {
    "Topics": ("topic", "T", 3),
    "Skills": ("skill", "S", 3),
    "Resources": ("resource", "R", 3),
    "Projects": ("project", "P", 3),
    "Templates": ("template", "TP", 3),
    "Maps": ("map", "M", 3),
    "FAQs": ("faq", "FAQ", 3),
    "Weekly-Logs": ("weekly", "WK", 3),
}

OPS_RULES = {
    "Demands": ("demand", "DEM", 4),
    "Pain-Points": ("pain", "PAIN", 4),
    "Defects": ("defect", "BUG", 3),
    "Validations": ("validation", "VAL", 3),
    "Handoffs": ("handoff", "HOF", 3),
    "Solutions": ("solution", "SOL", 3),
}

# 质量检查标准
QUALITY_CHECKS = {
    "has_metadata": lambda c: c.startswith("---"),
    "has_why_important": lambda c: bool(
        re.search(r"^##\s+为什么重要", c, re.MULTILINE)
    ),
    "has_core_content": lambda c: bool(re.search(r"^##\s+核心内容", c, re.MULTILINE)),
    "has_examples": lambda c: bool(re.search(r"^##\s+示例", c, re.MULTILINE)),
    "has_faq": lambda c: bool(re.search(r"^##\s+常见问题", c, re.MULTILINE)),
    "has_evaluation": lambda c: bool(re.search(r"多维度评估|质量评估", c)),
    "has_learning_path": lambda c: bool(re.search(r"学习路径", c)),
    "has_decision_matrix": lambda c: bool(re.search(r"决策矩阵 | 决策树", c)),
    "has_comparison": lambda c: bool(re.search(r"正误对比 | 对比", c)),
    "has_tags": lambda c: bool(re.search(r"##\s+标签", c)),
    "has_links": lambda c: len(re.findall(r"\[\[.+?\]\]", c)) >= 2,
    "has_tables": lambda c: len(re.findall(r"^\|.*\|$", c, re.MULTILINE)) >= 3,
}


class HealthChecker:
    """知识库健康度检查器"""

    def __init__(self, root: Path):
        self.root = root
        self.docs = []
        self.stats = {}

    def scan(self):
        """扫描所有文档"""
        print("开始扫描文档...")

        # 扫描主目录
        for dir_name, (entity_type, prefix, digits) in DIR_RULES.items():
            dir_path = self.root / dir_name
            if dir_path.exists():
                self._scan_directory(dir_path, entity_type, prefix, digits)

        # 扫描 Operations 目录
        ops_dir = self.root / "Operations"
        if ops_dir.exists():
            for dir_name, (entity_type, prefix, digits) in OPS_RULES.items():
                dir_path = ops_dir / dir_name
                if dir_path.exists():
                    self._scan_directory(dir_path, entity_type, prefix, digits)

        print(f"扫描完成，发现 {len(self.docs)} 个文档")

    def _scan_directory(
        self, dir_path: Path, entity_type: str, prefix: str, digits: int
    ):
        """扫描指定目录"""
        for md_file in sorted(dir_path.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")

            # 提取元数据
            metadata = self._extract_metadata(content)

            # 执行质量检查
            checks = {}
            for check_name, check_func in QUALITY_CHECKS.items():
                checks[check_name] = check_func(content)

            doc = {
                "file": md_file.name,
                "path": str(md_file.relative_to(self.root)),
                "entity_type": metadata.get("entity_type", entity_type),
                "entity_code": metadata.get("entity_code", "N/A"),
                "title": metadata.get("title", extract_title(content)),
                "lines": len(content.split("\n")),
                "tables": len(re.findall(r"^\|.*\|$", content, re.MULTILINE)),
                "links": len(re.findall(r"\[\[.+?\]\]", content)),
                "checks": checks,
                "score": self._calculate_score(checks),
                "status": "✅" if self._is_healthy(checks) else "⚠️",
            }
            self.docs.append(doc)

    def _extract_metadata(self, content: str) -> dict:
        """提取 YAML 元数据（简化版）"""
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if match:
            yaml_text = match.group(1)
            metadata = {}
            current_key = None
            current_list = None

            for line in yaml_text.split("\n"):
                line = line.strip()
                if not line:
                    continue

                if line.startswith("- "):
                    if current_key and current_list is not None:
                        current_list.append(line[2:].strip())
                    continue

                if ":" in line:
                    key, _, value = line.partition(":")
                    key = key.strip()
                    value = value.strip()

                    if value:
                        metadata[key] = value
                        current_key = None
                        current_list = None
                    else:
                        metadata[key] = []
                        current_key = key
                        current_list = metadata[key]

            return metadata
        return {}

    def _calculate_score(self, checks: dict) -> float:
        """计算文档质量分数"""
        weights = {
            "has_metadata": 0.1,
            "has_why_important": 0.1,
            "has_core_content": 0.1,
            "has_examples": 0.1,
            "has_faq": 0.1,
            "has_evaluation": 0.15,
            "has_learning_path": 0.1,
            "has_decision_matrix": 0.1,
            "has_comparison": 0.1,
            "has_tags": 0.05,
            "has_links": 0.05,
            "has_tables": 0.05,
        }

        score = sum(checks.get(k, False) * w for k, w in weights.items())
        return round(score, 2)

    def _is_healthy(self, checks: dict) -> bool:
        """判断文档是否健康"""
        # 必须满足的基本条件
        required = ["has_metadata", "has_why_important", "has_core_content", "has_tags"]
        optional = [
            "has_examples",
            "has_faq",
            "has_evaluation",
            "has_learning_path",
            "has_decision_matrix",
            "has_comparison",
            "has_links",
            "has_tables",
        ]

        # 检查必填项
        for req in required:
            if not checks.get(req, False):
                return False

        # 检查可选项（至少满足 50%）
        optional_met = sum(1 for opt in optional if checks.get(opt, False))
        return optional_met >= len(optional) // 2

    def generate_report(self):
        """生成健康度报告"""
        total = len(self.docs)
        healthy = sum(1 for d in self.docs if self._is_healthy(d["checks"]))

        # 按类型统计
        by_type = defaultdict(
            lambda: {"total": 0, "healthy": 0, "scores": [], "avg_score": 0}
        )
        for doc in self.docs:
            etype = doc["entity_type"]
            by_type[etype]["total"] += 1
            if self._is_healthy(doc["checks"]):
                by_type[etype]["healthy"] += 1
            by_type[etype]["scores"].append(doc["score"])

        for etype in by_type:
            scores = by_type[etype].pop("scores", [])
            by_type[etype]["avg_score"] = (
                round(sum(scores) / len(scores), 2) if scores else 0
            )

        # 检查未覆盖的维度
        missing_checks = defaultdict(int)
        for doc in self.docs:
            for check_name, passed in doc["checks"].items():
                if not passed:
                    missing_checks[check_name] += 1

        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_documents": total,
                "healthy_count": healthy,
                "health_rate": f"{healthy}/{total} ({healthy / total * 100:.1f}%)",
                "avg_score": round(sum(d["score"] for d in self.docs) / total, 2)
                if total
                else 0,
            },
            "by_type": dict(by_type),
            "missing_checks": dict(missing_checks),
            "low_quality_docs": [d for d in self.docs if d["score"] < 0.7],
            "recommendations": self._generate_recommendations(missing_checks, by_type),
        }

        return report

    def _generate_recommendations(self, missing_checks: dict, by_type: dict) -> list:
        """生成优化建议"""
        recommendations = []

        # 基于缺失检查项的建议
        if missing_checks.get("has_metadata", 0) > 0:
            recommendations.append(
                f"📝 元数据缺失：{missing_checks['has_metadata']}个文档缺少 YAML 头部"
            )
        if missing_checks.get("has_evaluation", 0) > 0:
            recommendations.append(
                f"📊 评估缺失：{missing_checks['has_evaluation']}个文档缺少多维度评估"
            )
        if missing_checks.get("has_learning_path", 0) > 0:
            recommendations.append(
                f"🛣️ 学习路径缺失：{missing_checks['has_learning_path']}个文档缺少学习路径"
            )
        if missing_checks.get("has_decision_matrix", 0) > 0:
            recommendations.append(
                f"🎯 决策矩阵缺失：{missing_checks['has_decision_matrix']}个文档缺少决策矩阵"
            )
        if missing_checks.get("has_comparison", 0) > 0:
            recommendations.append(
                f"↔️ 正误对比缺失：{missing_checks['has_comparison']}个文档缺少正误对比"
            )

        # 基于类型统计的建议
        for etype, stats in by_type.items():
            if stats["total"] > 0:
                rate = stats["healthy"] / stats["total"] * 100
                if rate < 80:
                    recommendations.append(
                        f"📈 {etype}: 健康率仅{rate:.1f}%，建议重点优化"
                    )

        return recommendations

    def save_report(self, report: dict, filename: str = None):
        """保存报告"""
        if not filename:
            filename = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 保存到 Reports 目录
        reports_dir = self.root / "Platform" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # JSON 格式
        json_file = reports_dir / f"{filename}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Markdown 格式
        md_lines = [
            "# 知识库健康度分析报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## 总览",
            "",
            "| 指标 | 值 |",
            "|------|-----|",
            f"| 文档总数 | {report['summary']['total_documents']} |",
            f"| 健康文档数 | {report['summary']['healthy_count']} |",
            f"| 健康率 | {report['summary']['health_rate']} |",
            f"| 平均质量分 | {report['summary']['avg_score']} |",
            "",
            "## 按类型统计",
            "",
            "| 类型 | 总数 | 健康数 | 健康率 | 平均分 |",
            "|------|------|--------|--------|--------|",
        ]

        for etype, stats in report["by_type"].items():
            rate = (
                f"{stats['healthy']}/{stats['total']} ({stats['healthy'] / stats['total'] * 100:.1f}%)"
                if stats["total"] > 0
                else "0/0 (0%)"
            )
            md_lines.append(
                f"| {etype} | {stats['total']} | {stats['healthy']} | {rate} | {stats['avg_score']} |"
            )

        md_lines.extend(
            [
                "",
                "## 缺失检查项",
                "",
                "| 检查项 | 缺失数量 |",
                "|--------|----------|",
            ]
        )

        for check, count in sorted(
            report["missing_checks"].items(), key=lambda x: -x[1]
        ):
            md_lines.append(f"| {check} | {count} |")

        md_lines.extend(
            [
                "",
                "## 优化建议",
                "",
            ]
        )

        for rec in report["recommendations"]:
            md_lines.append(f"- {rec}")

        md_lines.extend(
            [
                "",
                "## 低质量文档",
                "",
                "| 文件 | 类型 | 得分 | 状态 |",
                "|------|------|------|------|",
            ]
        )

        for doc in report["low_quality_docs"][:10]:
            md_lines.append(
                f"| {doc['file']} | {doc['entity_type']} | {doc['score']} | {doc['status']} |"
            )

        md_file = reports_dir / f"{filename}.md"
        md_file.write_text("\n".join(md_lines), encoding="utf-8")

        return json_file, md_file


def main():
    checker = HealthChecker(ROOT)

    if len(sys.argv) < 2 or sys.argv[1] == "scan":
        checker.scan()

    if len(sys.argv) < 2 or sys.argv[1] in ["scan", "report"]:
        report = checker.generate_report()
        json_file, md_file = checker.save_report(report)

        print("\n=== 健康度报告已生成 ===")
        print(f"JSON: {json_file}")
        print(f"MD: {md_file}")
        print(f"\n文档总数：{report['summary']['total_documents']}")
        print(f"健康文档：{report['summary']['healthy_count']}")
        print(f"健康率：{report['summary']['health_rate']}")
        print(f"平均分：{report['summary']['avg_score']}")

        if report["recommendations"]:
            print("\n优化建议:")
            for rec in report["recommendations"]:
                print(f"  {rec}")
    else:
        print(f"未知命令：{sys.argv[1]}")
        print("用法：python health_check.py [scan|report]")


if __name__ == "__main__":
    main()
