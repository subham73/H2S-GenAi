from langchain_core.tools import BaseTool
from typing import List, Dict
from core.data_models import HEALTHCARE_REGULATIONS

class ComplianceCheckerTool(BaseTool):
    name: str = "compliance_checker"
    description: str = "Validates test cases against regulatory requirements"

    def _run(self, test_cases: List[Dict], regulations: List[str]) -> List[Dict]:
        print("inside ComplianceCheckerTool _run")
        compliance_results = []
        for test_case in test_cases:
            for regulation in regulations:
                result = self._check_regulation_compliance(test_case, regulation)
                compliance_results.append(result)
        print("compliance_results from tool: ", compliance_results)
        return compliance_results

    def _check_regulation_compliance(self, test_case: Dict, regulation: str) -> Dict:
        violations = []
        recommendations = []
        risk_level = "Low"
        if regulation not in HEALTHCARE_REGULATIONS:
            return { 
                "test_case_id": test_case["id"],
                "regulation": regulation,
                "compliance_status": "Unknown",
                "violations": ["Regulation not in knowledge base"],
                "recommendations": ["Review regulation requirements manually"],
                "risk_level": "Medium"
            }
        reg_info = HEALTHCARE_REGULATIONS[regulation]
        if regulation == "HIPAA":
            violations, recommendations, risk_level = self._check_hipaa_compliance(test_case)
        elif regulation == "FDA_510K":
            violations, recommendations, risk_level = self._check_fda_510k_compliance(test_case)
        elif regulation == "IEC_62304":
            violations, recommendations, risk_level = self._check_iec_62304_compliance(test_case)
        elif regulation == "GDPR":
            violations, recommendations, risk_level = self._check_gdpr_compliance(test_case)
        compliance_status = "Non-Compliant" if violations else "Compliant"
        if not violations and not recommendations:
            compliance_status = "Fully Compliant"
        elif recommendations and not violations:
            compliance_status = "Compliant with Recommendations"
        return {
            "test_case_id": test_case["id"],
            "regulation": regulation,
            "compliance_status": compliance_status,
            "violations": violations,
            "recommendations": recommendations,
            "risk_level": risk_level
        }

    def _check_hipaa_compliance(self, test_case: Dict) -> tuple:
        violations, recommendations = [], []
        risk_level = "Low"
        if "patient" in test_case["description"].lower():
            if not any("encryption" in step.get("action", "").lower() for step in test_case["steps"]):
                violations.append("No encryption verification for PHI handling")
                risk_level = "High"
            if not any("audit" in step.get("action", "").lower() for step in test_case["steps"]):
                recommendations.append("Add audit log verification step")
        return violations, recommendations, risk_level

    def _check_fda_510k_compliance(self, test_case: Dict) -> tuple:
        violations, recommendations = [], []
        risk_level = "Low"
        if test_case["priority"] == "Critical":
            if not test_case.get("traceability_id", "").startswith("RISK"):
                recommendations.append("Link to risk analysis documentation")
        return violations, recommendations, risk_level

    def _check_iec_62304_compliance(self, test_case: Dict) -> tuple:
        violations, recommendations = [], []
        risk_level = "Low"
        if not test_case.get("regulatory_tags"):
            violations.append("No software safety classification specified")
            risk_level = "Medium"
        return violations, recommendations, risk_level

    def _check_gdpr_compliance(self, test_case: Dict) -> tuple:
        violations, recommendations = [], []
        risk_level = "Low"
        if "data" in test_case["description"].lower():
            if not any("consent" in step.get("action", "").lower() for step in test_case["steps"]):
                recommendations.append("Add consent verification step")
        return violations, recommendations, risk_level