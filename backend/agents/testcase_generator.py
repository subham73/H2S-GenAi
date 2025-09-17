from pydantic import ValidationError, Field
from core.data_models import QAState, ComplianceResult, RequirementAnalysis
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from tools.testcase_generator_tool import TestCaseGeneratorTool
from core.data_models import TestCase
from datetime import datetime
from dataclasses import dataclass
from pprint import pprint
from typing import List, Dict, Optional 
import uuid
import json
import re 

def extract_json(text: str) -> str:
    # Remove markdown-style code fences like ```json ... ```
    match = re.search(r"\[.*\]", text, re.DOTALL)
    return match.group(0) if match else ""


@dataclass
class TraceabilityMatrix:
    requirement_id: str
    requirement_text: str
    feature_ids: List[str]
    test_case_ids: List[str]

def parse_test_cases(test_cases_str: List[Dict]) -> List[TestCase]:
    try:
        data = json.loads(test_cases_str)
        test_cases = []
        for index, item in enumerate(data):
            tc = TestCase.model_validate(item)
            #TODO: add validation + tracibility
            test_cases.append(tc)
        return test_cases
    
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Error parsing test cases: {e}")
        return []

class TestCaseGeneratorAgent:
    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: QAState) -> QAState:
        state.current_step = "test_generation"
        state.messages.append(HumanMessage(content="Generating test cases"))
        print("Test case generator state at start: ")
        
        test_cases = await self._generate_testcases_with_llm(state.requirement_analysis)
        state.test_cases = test_cases

        print(f"Generated test cases")
        for tc in test_cases:
            pprint(tc)
        
        state.messages.append(AIMessage(content=f"Generated {len(test_cases)} test cases"))
        state.current_step = "compliance_check"
        print("state at end: ")
        return state
    
    async def _generate_testcases_with_llm(self, analysis: RequirementAnalysis) -> List[TestCase]:
        system_prompt = """
        You are a QA automation expert. Given the structured healthcare software requirement analysis below,
        generate comprehensive and non-overlapping blackbox test cases. 
        Cover each major area without missing workflows or creating duplicates.
        Use these sections specifically:
        1. functional_areas: Create functional test cases for each module understanding workflow and use case.
        2. security_considerations: Generate security test cases for each security aspect described.
        3. compliance_requirements: Generate compliance test cases verifying adherence to each regulation and its measures.
        4. data_handling: Include tests covering data collection, storage, transmission, retention, backup, and deletion policies.
        5. other_critical_aspects: Add tests for interoperability, integration points, performance, scalability, usability, and monitoring.

        Output the test cases as a JSON array [{...}], each test case having:
        {
            "id": unique test case identifier,
            "title": concise test case title,
            "description": test purpose,
            "preconditions": ["list of preconditions"],
            "steps": ["ordered list of test steps"],
            "expected_results": ["list of expected outcomes"],
            "priority": "test priority (e.g., High, Medium, Low)",
            "regulatory_tags": ["list of related regulation tags"]
        }
        Ensure clarity, avoid redundancy, and maintain flow of the testcases.
        """
        response = await self.llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Requirement Analysis: {analysis.model_dump_json(indent=2)}"),
        ])
        #response.content  ```json ... ``` -> string "[{...}, {...}]" -> json.loads -> List[Dict]
        raw_test_cases = extract_json(response.content) #string [{...}, {...}]
        try:
            structured_test_cases= parse_test_cases(raw_test_cases) # List[TestCase]
        except ValidationError as ve:
            ##TODO: will see later
            print("Validation error in test cases:", ve)
            structured_test_cases = []  # Return an empty 

        return structured_test_cases

