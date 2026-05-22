"""Skill Orchestrator — dynamic skill invocation during collaboration.

Invokes relevant skills at key points in the collaboration flow:
- Before Round 1: pre-retrieve related skills
- During Round 3 review: invoke validation skills (code-review, data-analysis)
- During Round 5 arbitration: invoke sedimentation skills
"""

import logging
from typing import Dict, List

logger = logging.getLogger("q-spectrum.skill-orchestrator")


class SkillOrchestrator:
    """
    在協作過程中動態調用技能，將結果匯入上下文。
    """

    SKILL_RULES = {
        "file-analyzer": ["文件", "file", "結構", "structure", "項目", "project"],
        "code-reviewer": ["代碼", "code", "審查", "review", "質量", "quality"],
        "data-processor": ["數據", "data", "CSV", "JSON", "處理", "process"],
        "project-planner": ["規劃", "plan", "計劃", "project plan"],
        "system-reporter": ["狀態", "status", "報告", "report", "系統", "system"],
    }

    def __init__(self, engine=None):
        self.engine = engine

    def match_skills_for_query(self, query: str) -> List[str]:
        """Match skills based on query keywords."""
        matched = []
        query_lower = query.lower()
        for skill_name, keywords in self.SKILL_RULES.items():
            if any(kw.lower() in query_lower for kw in keywords):
                matched.append(skill_name)
        return matched

    def orchestrate_for_collaboration(self, query: str,
                                       collaboration_context: Dict) -> Dict:
        """Orchestrate skills for collaboration context."""
        skills = self.match_skills_for_query(query)
        results = {}

        for skill_name in skills:
            result = self._execute_skill(skill_name, query, collaboration_context)
            results[skill_name] = result

        return results

    def _execute_skill(self, skill_name: str, query: str,
                        context: Dict) -> Dict:
        """Execute a single skill."""
        if not self.engine:
            return {"status": "error", "message": "Engine not available"}

        if hasattr(self.engine, 'real_skills') and self.engine.real_skills:
            try:
                result = self.engine.real_skills.execute(skill_name, query)
                if result.get("status") == "ok":
                    return result
            except Exception as e:
                logger.warning(f"Skill execution failed for {skill_name}: {e}")

        return {"status": "skipped", "message": f"Skill {skill_name} not available"}
