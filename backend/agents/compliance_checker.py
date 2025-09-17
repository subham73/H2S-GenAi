from backend.tools.compliance_checker_tool import ComplianceCheckerTool
from backend.core.data_models import QAState, ComplianceResult
from langchain_core.messages import HumanMessage, AIMessage
from pprint import pprint
class ComplianceCheckAgent:
    def __init__(self, llm):
        self.llm = llm
        self.tool = ComplianceCheckerTool()

    async def run(self, state: QAState) -> QAState:
        print("comming to compliance checking agent")
        state.current_step = "compliance_check"
        state.messages.append(HumanMessage(content="Checking compliance"))
        test_case_dicts = []
        for tc in state.test_cases:
            test_case_dicts.append({
                "id": tc.id,
                "title": tc.title,
                "description": tc.description,
                "preconditions": tc.preconditions,
                "steps": tc.steps,
                "expected_results": tc.expected_results,
                "priority": tc.priority,
                "regulatory_tags": tc.regulatory_tags,
                "traceability_id": tc.traceability_id
            })
        print("just before compliance tool call")
        compliance_result_dicts = self.tool.run(tool_input={
            "test_cases": test_case_dicts,
            "regulations": state.regulatory_requirements
        })
        print("after tool call compliance")
        compliance_results = []
        for cr_dict in compliance_result_dicts:
            compliance_result = ComplianceResult(
                test_case_id=cr_dict["test_case_id"],
                regulation=cr_dict["regulation"],
                compliance_status=cr_dict["compliance_status"],
                violations=cr_dict["violations"],
                recommendations=cr_dict["recommendations"],
                risk_level=cr_dict["risk_level"]
            )
            print("compliance")
            print(compliance_result)
            compliance_results.append(compliance_result)
        state.compliance_results = compliance_results
        for tc in state.test_cases:
            compliance_statuses = []
            for cr in compliance_results:
                if cr.test_case_id == tc.id:
                    compliance_statuses.append(cr.compliance_status)
            if compliance_statuses:
                if all(status in ["Compliant", "Fully Compliant", "Compliant with Recommendations"] 
                       for status in compliance_statuses):
                    tc.compliance_status = "Compliant"
                else:
                    tc.compliance_status = "Non-Compliant"
        state.messages.append(AIMessage(
            content=f"Compliance check completed. {len(compliance_results)} checks performed."
        ))
        print("state at compliance agent end: ")
        # pprint(state)
        state.current_step = "finalization"
        return state