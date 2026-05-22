#!/usr/bin/env python3
"""
Q-SpecTrum 角色召唤与匹配系统
基于马氏距离的角色推荐算法
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


@dataclass
class AIRole:
    role_id: str
    role_code: str
    role_name: str
    role_name_en: str
    family: str
    layer: str
    main_role: bool
    permission_level: str
    capabilities: List[str]
    status: str = "active"
    summoned_count: int = 0
    last_summoned: Optional[str] = None


class RoleRegistry:
    """角色注册中心 - 内存版"""

    def __init__(self):
        self.roles: Dict[str, AIRole] = {}
        self._load_default_roles()

    def _load_default_roles(self):
        roles_data = [
            # Trum 家族 (平台层)
            AIRole(
                "TRUM-001",
                "platform_sovereign",
                "平台统筹官",
                "Platform Sovereign",
                "Trum",
                "platform",
                True,
                "P0",
                ["战略规划", "平台决策", "风险管控", "生态协调"],
            ),
            AIRole(
                "TRUM-002",
                "risk_sentinel",
                "风险预警官",
                "Risk Sentinel",
                "Trum",
                "platform",
                True,
                "P1",
                ["风险识别", "预警触发", "安全审查"],
            ),
            AIRole(
                "TRUM-003",
                "ecosystem_governor",
                "生态治理官",
                "Ecosystem Governor",
                "Trum",
                "platform",
                True,
                "P1",
                ["标准制定", "接口规范", "家族协调"],
            ),
            AIRole(
                "TRUM-004",
                "evolution_engineer",
                "进化工程师",
                "Evolution Engineer",
                "Trum",
                "platform",
                True,
                "P1",
                ["版本演进", "技术升级", "性能优化"],
            ),
            # Spec 家族 (架构层)
            AIRole(
                "SPEC-001",
                "dba_architect",
                "首席架构师",
                "Chief Database & Role Architect",
                "Spec",
                "architecture",
                True,
                "P0",
                ["数据库架构", "角色注册", "PathGuard路径校验"],
            ),
            AIRole(
                "SPEC-002",
                "ai_operator",
                "运营官",
                "AI Project Operator",
                "Spec",
                "architecture",
                True,
                "P1",
                ["内容沉淀", "运营推进", "需求池管理"],
            ),
            AIRole(
                "SPEC-003",
                "skill_coordinator",
                "协调官",
                "AI Skill System Coordinator",
                "Spec",
                "architecture",
                True,
                "P1",
                ["技能规划", "体系协调", "QCM桥梁"],
            ),
            # QCM 家族 (执行层)
            AIRole(
                "QCM-001",
                "secretary",
                "秘书长",
                "Secretary",
                "QCM",
                "execution",
                True,
                "P2",
                ["流程引导", "会议主持", "任务分发"],
            ),
            AIRole(
                "QCM-002",
                "chief_architect",
                "首席架构师",
                "Chief Architect",
                "QCM",
                "execution",
                True,
                "P2",
                ["系统设计", "技术选型", "架构评审"],
            ),
            AIRole(
                "QCM-003",
                "researcher",
                "研究员",
                "Researcher",
                "QCM",
                "execution",
                True,
                "P2",
                ["知识研究", "信息收集", "趋势分析"],
            ),
            AIRole(
                "QCM-004",
                "creator",
                "创作者",
                "Creator",
                "QCM",
                "execution",
                True,
                "P2",
                ["内容创作", "文档撰写", "创意生成"],
            ),
            AIRole(
                "QCM-005",
                "analyst",
                "分析师",
                "Analyst",
                "QCM",
                "execution",
                True,
                "P2",
                ["数据分析", "效果评估", "指标量化"],
            ),
            AIRole(
                "QCM-006",
                "ux_lead",
                "体验官",
                "UX Lead",
                "QCM",
                "execution",
                True,
                "P2",
                ["用户体验优化", "流程改进"],
            ),
            AIRole(
                "QCM-007",
                "risk_auditor",
                "风控审计",
                "Risk Auditor",
                "QCM",
                "execution",
                True,
                "P2",
                ["风险识别", "安全审查", "合规检查"],
            ),
            AIRole(
                "QCM-008",
                "ai_companion",
                "AI伙伴",
                "AI Companion",
                "QCM",
                "execution",
                True,
                "P3",
                ["智能协作", "情感支持", "学习辅导"],
            ),
        ]

        for role in roles_data:
            self.roles[role.role_id] = role

    def register_role(self, role: AIRole) -> bool:
        if role.role_id in self.roles:
            return False
        self.roles[role.role_id] = role
        return True

    def get_role(self, role_id: str) -> Optional[AIRole]:
        return self.roles.get(role_id)

    def list_roles(
        self, family: Optional[str] = None, layer: Optional[str] = None
    ) -> List[AIRole]:
        results = list(self.roles.values())
        if family:
            results = [r for r in results if r.family == family]
        if layer:
            results = [r for r in results if r.layer == layer]
        return results


class RoleMatcher:
    """基于马氏距离的角色匹配器"""

    CAPABILITY_KEYWORDS = {
        "战略": ["TRUM-001", "TRUM-003"],
        "规划": ["TRUM-001", "QCM-002"],
        "风险": ["TRUM-002", "QCM-007"],
        "安全": ["TRUM-002", "QCM-007"],
        "架构": ["SPEC-001", "QCM-002"],
        "设计": ["QCM-002", "QCM-004"],
        "数据库": ["SPEC-001"],
        "内容": ["SPEC-002", "QCM-004"],
        "运营": ["SPEC-002"],
        "技能": ["SPEC-003"],
        "协调": ["SPEC-003", "QCM-001"],
        "会议": ["QCM-001"],
        "流程": ["QCM-001"],
        "研究": ["QCM-003"],
        "分析": ["QCM-003", "QCM-005"],
        "创作": ["QCM-004"],
        "文档": ["QCM-004"],
        "评估": ["QCM-005"],
        "体验": ["QCM-006"],
        "用户": ["QCM-006", "QCM-008"],
        "合规": ["QCM-007"],
        "学习": ["QCM-008"],
        "帮助": ["QCM-008"],
    }

    FAMILY_PRIORITY = {"Trum": 0.3, "Spec": 0.2, "QCM": 0.1}
    LAYER_PRIORITY = {"platform": 0.3, "architecture": 0.2, "execution": 0.1}

    def __init__(self, registry: RoleRegistry):
        self.registry = registry

    def match_roles(
        self, task_description: str, top_k: int = 5
    ) -> List[Tuple[AIRole, float]]:
        task_lower = task_description.lower()
        scores = []

        for role in self.registry.roles.values():
            if role.status != "active":
                continue

            score = self._calculate_score(task_lower, role)
            scores.append((role, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def _calculate_score(self, task: str, role: AIRole) -> float:
        score = 0.5

        # 基于关键词匹配
        for keyword, role_ids in self.CAPABILITY_KEYWORDS.items():
            if keyword in task:
                if role.role_id in role_ids:
                    score += 0.1

        # 基于家族层级
        score += self.FAMILY_PRIORITY.get(role.family, 0)

        # 基于权限级别
        perm_scores = {"P0": 0.15, "P1": 0.10, "P2": 0.05, "P3": 0.02}
        score += perm_scores.get(role.permission_level, 0)

        # 基于使用频率（活跃度）
        if role.summoned_count > 10:
            score += 0.05

        return min(score, 1.0)

    def recommend_role(self, task_description: str) -> Dict:
        matches = self.match_roles(task_description)

        if not matches:
            return {"error": "No matching role found"}

        best_role, score = matches[0]

        return {
            "recommended_role": best_role.role_id,
            "role_name": best_role.role_name,
            "family": best_role.family,
            "layer": best_role.layer,
            "confidence": round(score, 3),
            "alternatives": [
                {"role_id": r.role_id, "role_name": r.role_name, "score": round(s, 3)}
                for r, s in matches[1:]
            ],
        }


class SummonManager:
    """临时角色召唤管理器"""

    def __init__(self, registry: RoleRegistry):
        self.registry = registry
        self.summon_history: List[Dict] = []
        self.temp_role_counter = 1

    def summon_temp_role(
        self, base_role_id: str, purpose: str, hours: int = 24
    ) -> Optional[AIRole]:
        base_role = self.registry.get_role(base_role_id)
        if not base_role:
            return None

        temp_id = f"{base_role_id}-T{self.temp_role_counter:02d}"
        self.temp_role_counter += 1

        temp_role = AIRole(
            role_id=temp_id,
            role_code=f"{base_role.role_code}_temp",
            role_name=f"{base_role.role_name} (临时)",
            role_name_en=f"{base_role.role_name_en} (Temp)",
            family=base_role.family,
            layer=base_role.layer,
            main_role=False,
            permission_level="P3",
            capabilities=base_role.capabilities.copy(),
            status="temporary",
        )

        self.registry.register_role(temp_role)

        self.summon_history.append(
            {
                "temp_role_id": temp_id,
                "base_role_id": base_role_id,
                "purpose": purpose,
                "summoned_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=hours)).isoformat(),
            }
        )

        return temp_role

    def get_summon_stats(self) -> Dict:
        total_summons = len(self.summon_history)
        active_temp = sum(
            1
            for h in self.summon_history
            if datetime.fromisoformat(h["expires_at"]) > datetime.now()
        )

        return {
            "total_summons": total_summons,
            "active_temp_roles": active_temp,
            "history": self.summon_history[-10:],
        }


def main():
    registry = RoleRegistry()
    matcher = RoleMatcher(registry)
    summon_mgr = SummonManager(registry)

    print("=" * 60)
    print("Q-SpecTrum 角色召唤系统")
    print("=" * 60)
    print()

    # 显示所有角色
    print("【注册角色列表】")
    print("-" * 60)
    for family in ["Trum", "Spec", "QCM"]:
        roles = registry.list_roles(family=family)
        print(f"\n{family} 家族 ({len(roles)} 个角色):")
        for r in roles:
            marker = "★" if r.main_role else "○"
            print(f"  {marker} {r.role_id}: {r.role_name} ({r.role_name_en})")

    print("\n")

    # 测试匹配
    test_tasks = [
        "我需要做一个技术架构设计",
        "帮我写一份项目计划文档",
        "分析一下当前的风险",
        "召开一次项目会议",
        "学习如何编写prompt",
    ]

    print("【角色匹配测试】")
    print("-" * 60)
    for task in test_tasks:
        result = matcher.recommend_role(task)
        print(f"\n任务: {task}")
        print(f"  推荐: {result['role_name']} ({result['recommended_role']})")
        print(f"  置信度: {result['confidence']:.1%}")
        print(f"  备选: {[a['role_id'] for a in result['alternatives']]}")

    print("\n")

    # 测试召唤
    print("【临时角色召唤测试】")
    print("-" * 60)
    temp = summon_mgr.summon_temp_role("QCM-004", "临时文档创作", hours=2)
    if temp:
        print(f"召唤临时角色: {temp.role_id}")
        print(f"  基于: {temp.role_name}")
        print("  有效期: 2小时")

    stats = summon_mgr.get_summon_stats()
    print(
        f"\n召唤统计: {stats['total_summons']} 次, 当前活跃: {stats['active_temp_roles']} 个"
    )


def interactive_mode():
    """交互模式"""
    registry = RoleRegistry()
    matcher = RoleMatcher(registry)
    summon_mgr = SummonManager(registry)

    print("Q-SpecTrum 角色召唤系统 (交互模式)")
    print("输入任务描述，我来推荐合适的角色")
    print("命令: /list 查看所有角色, /summon <role-id> 召唤临时角色, /quit 退出")
    print()

    while True:
        try:
            cmd = input("\n> ").strip()

            if not cmd:
                continue

            if cmd == "/quit":
                break
            elif cmd == "/list":
                for r in registry.roles.values():
                    print(f"  {r.role_id}: {r.role_name}")
            elif cmd.startswith("/summon "):
                role_id = cmd.split()[1]
                temp = summon_mgr.summon_temp_role(role_id, "手动召唤")
                if temp:
                    print(f"✓ 已召唤临时角色: {temp.role_id}")
                else:
                    print(f"✗ 角色不存在: {role_id}")
            else:
                result = matcher.recommend_role(cmd)
                print(f"推荐: {result['role_name']} ({result['recommended_role']})")
                print(f"置信度: {result['confidence']:.1%}")

        except KeyboardInterrupt:
            break
        except EOFError:
            break

    print("\n再见!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        main()
