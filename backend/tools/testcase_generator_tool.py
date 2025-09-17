import uuid
from langchain_core.tools import BaseTool
from backend.core.data_models import HEALTHCARE_REGULATIONS 
from typing import List, Dict

class TestCaseGeneratorTool(BaseTool):
    name: str = "test_case_generator"
    description: str = "Generates comprehensive test cases from specifications"
    
    # def _run(self, tool_input: dict) -> List[Dict]:
    def _run(self, specification: str, regulatory_context: List[str]) -> List[Dict]:
        print("inside TestCaseGeneratorTool _run")
        # specification = tool_input.get("specification", "")
        print("specification received in tool: ", specification)
        # regulatory_context = tool_input.get("regulatory_context", [])
        print("regulatory_context received in tool: ", regulatory_context)
        features = self._extract_features(specification)
        test_cases = []
        for feature in features:
            functional_tc = self._create_functional_test_case(feature, regulatory_context)
            test_cases.append(functional_tc)
            if self._requires_security_testing(feature, regulatory_context):
                security_tc = self._create_security_test_case(feature, regulatory_context)
                test_cases.append(security_tc)
            compliance_tcs = self._create_compliance_test_cases(feature, regulatory_context)
            test_cases.extend(compliance_tcs)
        return test_cases

    def _extract_features(self, specification: str) -> List[str]:
        features = []
        if "patient data" in specification.lower():
            features.append("patient_data_handling")
        if "authentication" in specification.lower():
            features.append("user_authentication")
        if "reporting" in specification.lower():
            features.append("report_generation")
        if "integration" in specification.lower():
            features.append("system_integration")
        return features or ["core_functionality"]

    def _create_functional_test_case(self, feature: str, regulatory_context: List[str]) -> Dict:
        test_case_id = str(uuid.uuid4())
        return {
            "id": test_case_id,
            "title": f"Functional Test - {feature.replace('_', ' ').title()}",
            "description": f"Verify that {feature} works as specified",
            "preconditions": ["System is operational", "User has appropriate permissions"],
            "steps": [
                {"step": 1, "action": f"Navigate to {feature} module"},
                {"step": 2, "action": f"Execute {feature} operation"},
                {"step": 3, "action": "Verify results"}
            ],
            "expected_results": [f"{feature} executes successfully", "No errors displayed"],
            "priority": "High",
            "regulatory_tags": regulatory_context,
            "traceability_id": f"REQ-{feature.upper()}-001"
        }

    def _requires_security_testing(self, feature: str, regulatory_context: List[str]) -> bool:
        security_triggers = ["patient_data", "authentication", "integration"]
        return any(trigger in feature for trigger in security_triggers)

    def _create_security_test_case(self, feature: str, regulatory_context: List[str]) -> Dict:
        test_case_id = str(uuid.uuid4())
        return {
            "id": test_case_id,
            "title": f"Security Test - {feature.replace('_', ' ').title()}",
            "description": f"Verify security controls for {feature}",
            "preconditions": ["Security policies configured", "Test environment isolated"],
            "steps": [
                {"step": 1, "action": f"Attempt unauthorized access to {feature}"},
                {"step": 2, "action": "Verify access is denied"},
                {"step": 3, "action": "Check audit logs"}
            ],
            "expected_results": ["Access denied", "Security event logged"],
            "priority": "Critical",
            "regulatory_tags": regulatory_context + ["SECURITY"],
            "traceability_id": f"SEC-{feature.upper()}-001"
        }

    def _create_compliance_test_cases(self, feature: str, regulatory_context: List[str]) -> List[Dict]:
        compliance_cases = []
        for regulation in regulatory_context:
            if regulation in HEALTHCARE_REGULATIONS:
                test_case_id = str(uuid.uuid4())
                compliance_cases.append({
                    "id": test_case_id,
                    "title": f"{regulation} Compliance - {feature.replace('_', ' ').title()}",
                    "description": f"Verify {regulation} compliance for {feature}",
                    "preconditions": [f"{regulation} policies implemented"],
                    "steps": [
                        {"step": 1, "action": f"Review {regulation} requirements"},
                        {"step": 2, "action": f"Test {feature} against requirements"},
                        {"step": 3, "action": "Document compliance evidence"}
                    ],
                    "expected_results": [f"{regulation} requirements met"],
                    "priority": "Critical",
                    "regulatory_tags": [regulation],
                    "traceability_id": f"COMP-{regulation}-{feature.upper()}-001"
                })
        return compliance_cases