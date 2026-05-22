"""Hybrid Mode Router — decides between orchestrator and peer collaboration modes."""

from typing import Dict, Optional


class HybridModeRouter:
    """
    混合模式的路由器 — 決定每次請求走內環還是外環。

    判斷維度：
    1. 意圖類型（問答/創作/研究/設計/審計/協商）
    2. 複雜度評分（基於詞彙、概念數量、跨域程度）
    3. 風險等級（安全/架構/數據完整性）
    4. 知識缺口（本地知識是否足夠）
    5. 用戶階段（S1-S5，高級用戶更可能觸發外環）
    """

    INNER_LOOP_TRIGGERS = [
        "簡單問答", "角色體驗", "文件查詢", "狀態檢查",
        "日常對話", "技能調用（單一）", "配置查詢",
    ]

    OUTER_LOOP_TRIGGERS = [
        "架構設計", "多角色協商", "深度研究", "安全審計",
        "代碼審查（複雜）", "系統重構", "跨域問題",
        "知識缺口檢測", "用戶明確要求深度模式",
    ]

    FORCE_OUTER_KEYWORDS = [
        "深度", "全面", "多輪", "辯論", "協作",
        "deep", "comprehensive", "multi-round", "collaborate",
    ]

    FORCE_INNER_KEYWORDS = [
        "狀態", "查詢", "幫助", "你好",
        "status", "help", "hello", "hi",
    ]

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.threshold = self.config.get("mode_threshold", 0.6)
        self.max_rounds = self.config.get("max_collaboration_rounds", 5)

    def select_mode(self, user_input: str, context: Optional[Dict] = None) -> str:
        """
        返回 'orchestrator' 或 'peer'。
        """
        context = context or {}

        if any(kw in user_input.lower() for kw in self.FORCE_OUTER_KEYWORDS):
            return "peer"

        if any(kw in user_input.lower() for kw in self.FORCE_INNER_KEYWORDS):
            return "orchestrator"

        score = self._compute_complexity_score(user_input, context)

        return "peer" if score >= self.threshold else "orchestrator"

    def _compute_complexity_score(self, text: str, context: Dict) -> float:
        """
        綜合複雜度評分 0.0-1.0。
        """
        scores = {}

        words = text.split()
        scores["lexical"] = min(1.0, len(words) / 30)

        cross_domain = self._count_cross_domain_concepts(text)
        scores["conceptual"] = min(1.0, cross_domain / 5)

        scores["risk"] = self._assess_risk(text)

        scores["knowledge_gap"] = self._estimate_knowledge_gap(text)

        weights = {
            "lexical": 0.15,
            "conceptual": 0.35,
            "risk": 0.30,
            "knowledge_gap": 0.20,
        }
        return sum(scores[k] * weights[k] for k in weights)

    def _count_cross_domain_concepts(self, text: str) -> int:
        """Count cross-domain concepts in text."""
        domain_keywords = {
            "architecture": ["架構", "architecture", "distributed", "分佈式", "microservice"],
            "security": ["安全", "security", "risk", "風險", "threat", "威脅"],
            "data": ["數據", "data", "database", "數據庫", "schema"],
            "ai": ["AI", "模型", "model", "LLM", "訓練", "training"],
            "devops": ["部署", "deploy", "CI/CD", "運維", "ops"],
        }

        text_lower = text.lower()
        domains_hit = 0
        for domain, keywords in domain_keywords.items():
            if any(kw.lower() in text_lower for kw in keywords):
                domains_hit += 1
        return domains_hit

    def _assess_risk(self, text: str) -> float:
        """Assess risk level 0.0-1.0."""
        risk_keywords = [
            "安全", "security", "風險", "risk", "漏洞", "vulnerability",
            "刪除", "delete", "drop", "destroy", "破壞",
            "生產", "production", "線上", "live",
        ]
        text_lower = text.lower()
        hits = sum(1 for kw in risk_keywords if kw.lower() in text_lower)
        return min(1.0, hits / 3)

    def _estimate_knowledge_gap(self, text: str) -> float:
        """Estimate knowledge gap 0.0-1.0 (higher = more gap)."""
        technical_indicators = [
            "最新", "latest", "2024", "2025", "2026",
            "benchmark", "comparison", "比較",
            "how to", "怎麼", "如何", "最佳實踐", "best practice",
        ]
        text_lower = text.lower()
        hits = sum(1 for ind in technical_indicators if ind.lower() in text_lower)
        return min(1.0, hits / 2)
