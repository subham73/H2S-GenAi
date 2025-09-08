from core.data_models import QAState, ComplianceResult
from langchain_core.messages import HumanMessage, AIMessage
from tools.testcase_generator_tool import TestCaseGeneratorTool
from core.data_models import TestCase
from datetime import datetime
from pprint import pprint


class TestCaseGeneratorAgent:
    def __init__(self, llm):
        self.llm = llm
        self.tool = TestCaseGeneratorTool()

    async def run(self, state: QAState) -> QAState:
        state.current_step = "test_generation"
        state.messages.append(HumanMessage(content="Generating test cases"))
        print("Test case generator state at start: ", )
        # pprint(state)
        print("just before tool call")
        test_case_dicts = self.tool.run(tool_input={
            "specification":state.specification,
            "regulatory_context": state.regulatory_requirements
        })
        test_cases = []
        print("inside testcase agent , just after tool call")
        for tc_dict in test_case_dicts:
            test_case = TestCase(
                id=tc_dict["id"],
                title=tc_dict["title"],
                description=tc_dict["description"],
                preconditions=tc_dict["preconditions"],
                steps=tc_dict["steps"],
                expected_results=tc_dict["expected_results"],
                priority=tc_dict["priority"],
                regulatory_tags=tc_dict["regulatory_tags"],
                traceability_id=tc_dict["traceability_id"],
                created_at=datetime.now()
            )
            print("test case..")
            print(test_case)
            test_cases.append(test_case)
        state.test_cases = test_cases
        # print("inside testcaseagent, Test case generator state at end: ", test_cases)
        state.messages.append(AIMessage(content=f"Generated {len(test_cases)} test cases"))
        state.current_step = "compliance_check"
        print("state at end: ")
        pprint(state)
        return state