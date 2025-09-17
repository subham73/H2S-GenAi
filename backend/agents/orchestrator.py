import json
import re
from backend.core.data_models import QAState, ComplianceResult, RequirementAnalysis
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import List, Dict, Optional
from pprint import pprint
from pydantic import BaseModel, ValidationError, Field

def extract_json(text: str) -> str:
    # Remove markdown-style code fences like ```json ... ```
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else ""

# class RequirementAnalysis(BaseModel):
#     functional_areas: List[str]
#     security_considerations: List[str]
#     compliance_requirements: List[str]
#     data_handling: List[str]
#     other_critical_aspects: List[str]



class OrchestratorAgent:
    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: QAState) -> QAState:
        state.messages.append(HumanMessage(content="Starting QA automation workflow"))
        state.current_step = "orchestration"

        state.requirement_analysis = await self._analyze_requirement(state.requirement)
        print("Orch Agent, analysis : ", state.requirement_analysis)

        if not state.regulatory_requirements: # If regulatory not provided, extract from requirement
            state.regulatory_requirements = self._extract_regulatory_requirements(state.requirement_analysis.compliance_requirements)
        print("Orch Agent, state.regulatory_requirements : ", state.regulatory_requirements )
        
        # workflow_plan = self._create_workflow_plan(analysis, state.regulatory_requirements)
        # print("Orch Agent, workflow_plan : ", workflow_plan )
        # state.messages.append(AIMessage(content=f"Workflow plan created: {workflow_plan}"))
        # No need for workflow plan now
        
        state.current_step = "test_generation"
        print("orchestrator state at end")
        return state

    async def _analyze_requirement(self, requirement: str) -> RequirementAnalysis:
        system_prompt = """
        You are an expert in analyzing healthcare software requirements. 
        Return a JSON object exactly matching this schema:
        If some information is not available or not applicable, leave the corresponding field blank or empty (empty list or empty string).
        {
            "functional_areas": {
                "modules": [list of main modules],
                "workflows": [list of key workflows],
                "use_cases": [list of important use cases]
            },
            "security_considerations": {
                "data_protection": "description of data protection measures",
                "user_authentication": "description of user authentication",
                "authorization": "description of authorization policies",
                "access_control": "description of access control mechanisms",
                "logging": "description of logging practices",
                "incident_detection": "description of incident detection"
            },
            "compliance_requirements": {
                "regulations": [list of relevant regulations, e.g., HIPAA, GDPR],
                "compliance_measures": {
                "HIPAA": "explanation of HIPAA compliance measures",
                "GDPR": "explanation of GDPR compliance measures"
                /* Add other regulations as applicable */
                },
                "auditability": "description of audit practices"
            },
            "data_handling": {
                "data_entities": [list of data entities such as patient records],
                "data_collection": "description of data collection methods",
                "data_storage": "description of data storage mechanisms",
                "data_transmission": "description of data transmission security",
                "retention_policy": "data retention policies",
                "backup_policy": "data backup procedures",
                "deletion_policy": "data deletion rules"
            },
            "other_critical_aspects": {
                "interoperability": "description of interoperability standards",
                "integration": "description of integration points with other systems",
                "performance": "performance expectations",
                "scalability": "scalability considerations",
                "usability": "usability factors",
                "monitoring": "system monitoring procedures"
            }
        }
        Do not include markdown formatting, explanations, or any text outside the JSON object.
        """
        response = await self.llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=requirement),
        ])

        raw_analysis_str = extract_json(response.content) #string
        print("inside orch, llm_raw_analysis : ", raw_analysis_str)
        raw_analysis = json.loads(raw_analysis_str) #dict 
        try: 
            structured_analysis = RequirementAnalysis.model_validate(raw_analysis)
        except ValidationError as ve:
            ##TODO: will see later 
            print("Validation error in requirement analysis:", ve)
            structured_analysis = RequirementAnalysis()  # Return an empty analysis on validation error

        return structured_analysis

    def _extract_regulatory_requirements(self, compliance_requirements: str) -> List[str]:
        regulations = []
        spec_lower = compliance_requirements.lower()

        if "hipaa" in spec_lower or "patient" in spec_lower:
            regulations.append("HIPAA")
        if "fda" in spec_lower or "medical device" in spec_lower:
            regulations.append("FDA_510K")
        if "iec" in spec_lower or "software lifecycle" in spec_lower:
            regulations.append("IEC_62304")
        if "gdpr" in spec_lower or "data protection" in spec_lower:
            regulations.append("GDPR")
        if "iso" in spec_lower:
            regulations.append("ISO_13485")
        if not regulations:
            regulations.append("HIPAA") # TODO: Default to HIPAA if none found 
        return regulations

    # def _create_workflow_plan(self, analysis: Dict, regulations: List[str]) -> Dict:
    #     # TODO : Hard linked now , later if testcases comes in it wll go for gap check and compliance check  
    #     return {
    #         "steps": ["test_generation", "compliance_check", "finalization"],
    #         "estimated_test_cases": len(analysis["functional_areas"]) * 3,
    #         "compliance_checks": len(regulations),
    #         "priority": "high" if "Critical" in str(analysis) else "medium"
    #     }