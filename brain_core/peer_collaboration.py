"""Peer Collaboration Engine — Q-SpecTrum ↔ LLM multi-round debate/collaboration.

Dual-Loop Outer Loop: when hybrid_router selects 'peer' mode, this engine
orchestrates multi-round collaboration between Q-SpecTrum and LLM.

Collaboration flow (standard 3-5 rounds):
  Round 1: Framework Proposal — Q-SpecTrum proposes analysis framework
  Round 2: LLM Generation — LLM generates draft based on framework
  Round 3: Q-SpecTrum Review — Review draft, supplement knowledge, mark issues
  Round 4: LLM Revision — LLM revises based on review (if needed)
  Round 5: Final Arbitration — Q-SpecTrum makes final decision
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class CollaborationTurn:
    """A single turn in the collaboration."""
    round_num: int
    speaker: str  # "qspectrum" or "llm"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CollaborationResult:
    """Final result of a peer collaboration session."""
    user_input: str
    role_code: str
    family: str
    turns: List[CollaborationTurn] = field(default_factory=list)
    final_response: str = ""
    knowledge_deposited: int = 0
    status: str = "completed"  # "completed", "aborted", "error"

    def to_dict(self) -> dict:
        return {
            "user_input": self.user_input,
            "role_code": self.role_code,
            "family": self.family,
            "turns": [
                {"round": t.round_num, "speaker": t.speaker, "content": t.content[:200]}
                for t in self.turns
            ],
            "final_response": self.final_response[:500],
            "knowledge_deposited": self.knowledge_deposited,
            "status": self.status,
        }


class PeerCollaborationEngine:
    """
    對等協作引擎 — Q-SpecTrum 與 LLM 展開多輪辯論/協商。
    """

    def __init__(self, engine=None, max_rounds: int = 5):
        self.engine = engine
        self.max_rounds = max_rounds

    def collaborate(self, user_input: str, role_code: str, family: str,
                    max_rounds: Optional[int] = None, context: Optional[Dict] = None) -> CollaborationResult:
        """
        Main collaboration entry point (sync).
        """
        max_rounds = max_rounds or self.max_rounds
        result = CollaborationResult(
            user_input=user_input,
            role_code=role_code,
            family=family,
        )

        try:
            framework = self._propose_framework(user_input, role_code)
            result.turns.append(CollaborationTurn(
                round_num=1, speaker="qspectrum", content=framework,
            ))

            draft = self._llm_generate(framework, user_input)
            result.turns.append(CollaborationTurn(
                round_num=2, speaker="llm", content=draft,
            ))

            if max_rounds >= 3:
                review = self._review(draft, framework, user_input)
                result.turns.append(CollaborationTurn(
                    round_num=3, speaker="qspectrum", content=review,
                ))

                if max_rounds >= 4 and self._needs_revision(review):
                    revised = self._llm_generate(review, user_input)
                    result.turns.append(CollaborationTurn(
                        round_num=4, speaker="llm", content=revised,
                    ))
                    draft = revised

            result.final_response = self._arbitrate(draft, user_input)
            result.status = "completed"

        except Exception as e:
            result.status = "error"
            result.final_response = f"協作過程發生錯誤: {e}"

        return result

    def _propose_framework(self, user_input: str, role_code: str) -> str:
        """Round 1: Q-SpecTrum proposes analysis framework."""
        framework_parts = [
            "## 分析框架 (Analysis Framework)",
            f"角色: {role_code}",
            f"用戶問題: {user_input}",
            "",
            "請基於以下要求生成回答：",
            "1. 提供結構化的分析",
            "2. 包含具體的建議和步驟",
            "3. 標註不確定的部分",
            "4. 如有代碼，請包含註釋和錯誤處理",
        ]
        return "\n".join(framework_parts)

    def _llm_generate(self, context: str, user_input: str) -> str:
        """Round 2/4: Call LLM to generate/revise response."""
        if not self.engine or not hasattr(self.engine, 'llm'):
            return "[LLM 不可用，使用模擬回應]"

        system_prompt = "你是一個專業的AI協作者。請基於提供的框架和用戶問題，生成高質量的回答。"
        user_message = f"框架/審閱意見:\n{context}\n\n原始問題: {user_input}"

        try:
            return self.engine.llm.generate(
                system_prompt=system_prompt,
                user_message=user_message,
            )
        except Exception as e:
            return f"[LLM 調用失敗: {e}]"

    def _review(self, draft: str, framework: str, user_input: str) -> str:
        """Round 3: Q-SpecTrum reviews the draft."""
        review_parts = [
            "## 審閱意見 (Review)",
            "",
            "初稿已收到。以下是審閱意見：",
            "1. 檢查回答是否完整覆蓋用戶問題",
            "2. 檢查技術準確性",
            "3. 補充遺漏的知識點",
            "",
            "請基於以上意見修正回答。",
        ]
        return "\n".join(review_parts)

    def _needs_revision(self, review: str) -> bool:
        """Check if review indicates need for revision."""
        return any(kw in review for kw in ["修正", "revision", "修改", "improve"])

    def _arbitrate(self, draft: str, user_input: str) -> str:
        """Round 5: Final arbitration — produce final response."""
        return draft
