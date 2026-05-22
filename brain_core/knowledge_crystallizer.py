"""Knowledge Crystallizer — extract decisions and deposit to memory.

Crystallization flow:
  1. Decision Extraction — extract key decisions from collaboration turns
  2. Verification — verify knowledge correctness
  3. Dedup + Link — remove duplicates, link to existing knowledge
  4. Deposit — write to memory system
  5. Graph Update — update knowledge graph
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Decision:
    """A crystallized decision from collaboration."""
    summary: str
    content: str
    priority: str  # "P0", "P1", "P2", "P3"
    source: str  # "collaboration", "review", "arbitration"
    verified: bool = False


class KnowledgeCrystallizer:
    """
    將協作結果沉澱為 P0-P1 知識。
    """

    def __init__(self, engine=None):
        self.engine = engine

    def crystallize(self, collaboration_result) -> List[Decision]:
        """Crystallize knowledge from collaboration result."""
        decisions = self._extract_decisions(collaboration_result)
        verified = self._verify(decisions)
        deposited = []

        for decision in verified:
            if decision.priority in ("P0", "P1"):
                self._deposit(decision, collaboration_result)
                deposited.append(decision)

        return deposited

    def _extract_decisions(self, collaboration_result) -> List[Decision]:
        """Extract key decisions from collaboration turns."""
        decisions = []

        if collaboration_result.final_response:
            decisions.append(Decision(
                summary=f"協作最終回應 ({collaboration_result.role_code})",
                content=collaboration_result.final_response[:500],
                priority="P1",
                source="arbitration",
            ))

        for turn in collaboration_result.turns:
            if turn.speaker == "qspectrum" and turn.round_num >= 3:
                decisions.append(Decision(
                    summary=f"審閱意見 (Round {turn.round_num})",
                    content=turn.content[:300],
                    priority="P2",
                    source="review",
                ))

        return decisions

    def _verify(self, decisions: List[Decision]) -> List[Decision]:
        """Verify decisions (simple heuristic for now)."""
        for decision in decisions:
            decision.verified = len(decision.content) > 20
        return decisions

    def _deposit(self, decision: Decision, collaboration_result) -> None:
        """Deposit decision to memory system."""
        if self.engine and hasattr(self.engine, 'knowledge'):
            try:
                self.engine.knowledge.deposit(
                    query=decision.summary,
                    response=decision.content,
                    role_code=collaboration_result.role_code,
                    family=collaboration_result.family,
                )
                collaboration_result.knowledge_deposited += 1
            except Exception:
                pass
