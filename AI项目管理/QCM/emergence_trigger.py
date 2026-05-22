#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q-SpecTrum Emergence Trigger Engine
Monitors R-value and triggers emergence when threshold reached
优化版 - 对齐super_brain_v2.py的R公式
"""

import os
import sys
from datetime import datetime
from typing import Dict, Tuple

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 路径配置
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class EmergenceTrigger:
    def __init__(self):
        # 优化版R公式权重 - 对齐super_brain_v2.py
        self.K_SIM_WEIGHT = 0.35
        self.C_COMP_WEIGHT = 0.30  # 强化互补性
        self.I_FREQ_WEIGHT = 0.25
        self.E_DIV_WEIGHT = 0.10  # 降低惩罚
        self.THRESHOLD = 0.85

# Domain knowledge base - 完全复制super_brain_v2.py的domains
        self.domain_db = {
            "飞轮迭代": {
                "keywords": ["飞轮迭代", "迭代", "6阶段", "scan", "diagnose", "execute", "crystallize",
                          "自我进化", "循环", "改进", "优化", "评估", "成长", "进化", "提升",
                          "累积", "加速", "势能", "反馈", "复盘", "迭代", "循环", "改进"],
                "complement": ["知识结晶", "费曼卡片", "涌现触发", "自检", "MEMORY", "知识共振", "技能系统"],
                "search_alias": ["flywheel iteration", "PDCA", "continuous improvement"],
                "interaction_count": 10,
                "stability": 0.85
            },
            "费曼卡片": {
                "keywords": ["费曼卡片", "知识结晶", "simple", "teach", "learning", "卡片",
                          "简化", "理解", "教学", "传承", "内化", "吸收", "固化",
                          "记忆", "概念", "模型", "框架", "方法论", "费曼", "学习"],
                "complement": ["飞轮迭代", "涌现触发", "技能系统", "MEMORY", "知识共振", "自我进化"],
                "search_alias": ["Feynman technique", "knowledge crystallization"],
                "interaction_count": 12,
                "stability": 0.88
            },
            "涌现触发": {
                "keywords": ["涌现触发", "R值", "共振", "emergence", "新能力", "触发",
                          "涌现", "创新", "突破", "突变", "质变", "突破",
                          "连接", "协同", "整合", "融合", "涌现", "创新", "质变"],
                "complement": ["费曼卡片", "知识共振", "飞轮迭代", "自检", "MEMORY", "知识结晶"],
                "search_alias": ["emergence", "system emergence", "self-organization"],
                "interaction_count": 8,
                "stability": 0.75
            },
            "知识共振": {
                "keywords": ["知识共振", "知识网络", "resonance", "连接", "整合",
                          "共振", "协同", "融合", "关系", "网络", "链接",
                          "图谱", "关联", "匹配", "共振", "共鸣", "协同", "整合"],
                "complement": ["涌现触发", "知识图谱", "MEMORY", "费曼卡片", "飞轮迭代", "自我进化"],
                "search_alias": ["knowledge resonance", "knowledge graph"],
                "interaction_count": 9,
                "stability": 0.82
            },
            "自检": {
                "keywords": ["自检", "诊断", "验证", "check", "健康度",
                          "监控", "评估", "修复", "扫描", "检查", "验证",
                          "测试", "校验", "审视", "反思", "诊断", "健康"],
                "complement": ["飞轮迭代", "涌现触发", "自动化", "MEMORY", "知识共振", "费曼卡片"],
                "search_alias": ["self-check", "system health monitor"],
                "interaction_count": 7,
                "stability": 0.80
            },
            "MEMORY": {
                "keywords": ["MEMORY", "长期记忆", "memory", "记忆", "状态",
                          "context", "跨会话", "传承", "存储", "积累",
                          "记录", "日志", "历史", "痕迹", "传承", "记忆", "上下文"],
                "complement": ["知识共振", "知识图谱", "费曼卡片", "飞轮迭代", "自检", "涌现触发"],
                "search_alias": ["long-term memory", "context management"],
                "interaction_count": 11,
                "stability": 0.90
            },
            "知识图谱": {
                "keywords": ["知识图谱", "图谱", "knowledge", "graph", "节点", "边",
                          "关系", "结构", "网络", "知识", "本体", "语义"],
                "complement": ["知识共振", "MEMORY", "涌现触发", "费曼卡片"],
                "search_alias": ["knowledge graph", "ontology"],
                "interaction_count": 8,
                "stability": 0.85
            },
            "技能系统": {
                "keywords": ["技能系统", "技能", "能力", "skill", "扩展", "模块",
                          "组合", "工具", "方法", "技术", "专长", "能力"],
                "complement": ["费曼卡片", "飞轮迭代", "场景", "角色", "知识结晶"],
                "search_alias": ["skill system", "capability"],
                "interaction_count": 6,
                "stability": 0.78
            }
        }

    def calculate_r(self, k_sim: float, c_comp: float, i_freq: float, e_div: float) -> float:
        """计算R值 - 优化版"""
        r = (self.K_SIM_WEIGHT * k_sim +
             self.C_COMP_WEIGHT * c_comp +
             self.I_FREQ_WEIGHT * i_freq -
             self.E_DIV_WEIGHT * e_div)
        return min(max(r, 0), 1.0)

    def calculate_domain_r(self, domain1: str, domain2: str) -> Tuple[float, Dict]:
        """Calculate R-value between two domains - 优化版"""
        if domain1 not in self.domain_db or domain2 not in self.domain_db:
            return 0.5, {}

        d1 = self.domain_db[domain1]
        d2 = self.domain_db[domain2]

        # K_sim - 知识相似度 (强化)
        common = set(d1["keywords"]) & set(d2["keywords"])
        k_sim = min(max(len(common) / 3, 0.50), 1.0)

        # C_comp - 互补性 (强化)
        c1 = len([c for c in d1["complement"] if c == domain2])
        c2 = len([c for c in d2["complement"] if c == domain1])
        c_comp = min(max((c1 + c2 + 3) / 5, 0.60), 1.0)

        # I_freq - 交互频率
        i1 = d1.get("interaction_count", 1)
        i2 = d2.get("interaction_count", 1)
        i_freq = min(0.80 + (i1 + i2) / 40, 0.95)

        # E_div - 熵散度 (降低惩罚)
        s1 = d1.get("stability", 0.8)
        s2 = d2.get("stability", 0.8)
        e_div = 0.20 - ((s1 + s2) / 2 - 0.8) * 0.25
        e_div = max(0.10, min(e_div, 0.25))

        r = self.calculate_r(k_sim, c_comp, i_freq, e_div)

        details = {
            "domain1": domain1,
            "domain2": domain2,
            "k_sim": k_sim,
            "c_comp": c_comp,
            "i_freq": i_freq,
            "e_div": e_div,
            "r": r
        }

        return r, details

    def check_emergence(self) -> Dict:
        """Check if emergence is triggered"""
        combinations = [
            ("飞轮迭代", "费曼卡片"),
            ("飞轮迭代", "涌现触发"),
            ("飞轮迭代", "自检"),
            ("飞轮迭代", "MEMORY"),
            ("知识共振", "知识图谱"),
            ("费曼卡片", "涌现触发"),
            ("自检", "飞轮迭代"),
            ("飞轮迭代", "知识共振"),
        ]

        results = []
        max_r = 0
        best_combo = None

        for combo in combinations:
            r, details = self.calculate_domain_r(combo[0], combo[1])
            results.append({
                "combo": combo,
                "r": r,
                "details": details
            })
            if r > max_r:
                max_r = r
                best_combo = combo

        triggered = max_r >= self.THRESHOLD

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "threshold": self.THRESHOLD,
            "max_r": max_r,
            "best_combo": best_combo,
            "triggered": triggered,
            "all_results": results
        }

    def run(self):
        """Run emergence check"""
        print("=" * 60)
        print("Q-SpecTrum Emergence Trigger")
        print("=" * 60)

        result = self.check_emergence()

        print(f"\n[TIME] {result['timestamp']}")
        print("\n[EMERGENCE CHECK]")
        print(f"  Threshold: R >= {result['threshold']}")
        print(f"  Current Max R: {result['max_r']:.3f}")
        print(f"  Best Combo: {result['best_combo']}")

        print("\n[R-VALUE BY COMBO]")
        for r in result['all_results']:
            status = "[OK]" if r['r'] >= 0.85 else "[WARN]" if r['r'] >= 0.80 else "[---]"
            combo_str = " + ".join(r['combo'])
            print(f"  {status} {combo_str}: R={r['r']:.3f}")

        print("\n" + "=" * 60)
        if result['triggered']:
            print("[OK] Emergence triggered!")
        else:
            print(f"[WARN] Not triggered (gap: {result['threshold'] - result['max_r']:.3f})")
            print("[TIP] Increase interaction frequency between domains")
        print("=" * 60)

        return result

if __name__ == "__main__":
    trigger = EmergenceTrigger()
    trigger.run()
