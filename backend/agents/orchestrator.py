from core.data_models import QAState, ComplianceResult
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Dict
from pprint import pprint
class OrchestratorAgent:
    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: QAState) -> QAState:
        state.messages.append(HumanMessage(content="Starting QA automation workflow"))
        state.current_step = "orchestration"
        analysis = await self._analyze_specification(state.specification)
        print("inside orch, analysis : ", analysis )
        if not state.regulatory_requirements:
            state.regulatory_requirements = self._extract_regulatory_requirements(state.specification)
        print("inside orch, state.regulatory_requirements : ", state.regulatory_requirements )
        workflow_plan = self._create_workflow_plan(analysis, state.regulatory_requirements)
        print("inside orch, workflow_plan : ", workflow_plan )
        state.messages.append(AIMessage(content=f"Workflow plan created: {workflow_plan}"))
        state.current_step = "test_generation"
        print("orchestrator state at end: ")
        # pprint(state)
        return state

    async def _analyze_specification(self, specification: str) -> Dict:
        prompt = f"""
        Analyze this healthcare software specification and identify:
        1. Key functional areas
        2. Data handling requirements
        3. Integration points
        4. Security considerations

        Specification: {specification}

        Provide a structured analysis.
        """
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        # Stub: parse response for demo. In real usage, parse LLM output here.
        return {
            "functional_areas": ["patient_management", "data_processing", "reporting"],
            "data_requirements": ["PHI_handling", "audit_trails"],
            "integration_points": ["EHR_systems", "lab_interfaces"],
            "security_needs": ["authentication", "encryption", "access_control"]
        }

    def _extract_regulatory_requirements(self, specification: str) -> List[str]:
        regulations = []
        spec_lower = specification.lower()
        if "hipaa" in spec_lower or "patient" in spec_lower:
            regulations.append("HIPAA")
        if "fda" in spec_lower or "medical device" in spec_lower:
            regulations.append("FDA_510K")
        if "iec" in spec_lower or "software lifecycle" in spec_lower:
            regulations.append("IEC_62304")
        if "gdpr" in spec_lower or "data protection" in spec_lower:
            regulations.append("GDPR")
        if not regulations:
            regulations.append("HIPAA")
        return regulations

    def _create_workflow_plan(self, analysis: Dict, regulations: List[str]) -> Dict:
        return {
            "steps": ["test_generation", "compliance_check", "finalization"],
            "estimated_test_cases": len(analysis["functional_areas"]) * 3,
            "compliance_checks": len(regulations),
            "priority": "high" if "Critical" in str(analysis) else "medium"
        }