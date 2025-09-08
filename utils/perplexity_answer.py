To fully integrate the advanced feature extraction, test case generation, and traceability matrix logic from your first (long) prototype code into your current streamlined `TestCaseGeneratorTool` class, you should:

1. **Replace basic feature extraction with dataclass-based extraction and inference.**  
2. **Generate detailed test cases per extracted feature, not just per keyword string.**
3. **Add traceability matrix generation as part of the tool.**
4. **Ensure you use structured objects (`Feature`, `TestCase`, etc.) and connect requirements to both features and test cases.**

Below is a refactored version of your `TestCaseGeneratorTool` which integrates the main elements: dataclasses, feature extraction, test case generation, traceability management, and regulatory tagging. Place this logic in the tool class directly, replacing your older prototype logic and method signatures.

```python
import uuid
from dataclasses import dataclass
from typing import List, Dict, Any
from core.data_models import HEALTHCARE_REGULATIONS
from langchain_core.tools import BaseTool

# Dataclasses for feature, testcase, traceability
@dataclass
class Feature:
    id: str
    name: str
    actors: List[str]
    actions: List[str]
    data: List[str]
    business_rules: List[str]
    priority: str
    complexity: str

@dataclass
class TestCase:
    id: str
    title: str
    feature_id: str
    description: str
    steps: List[str]
    expected: List[str]
    priority: str
    traceability_id: str

@dataclass
class TraceabilityMatrix:
    requirement_id: str
    requirement_text: str
    feature_ids: List[str]
    test_case_ids: List[str]

class TestCaseGeneratorTool(BaseTool):
    name: str = "test_case_generator"
    description: str = "Generates comprehensive test cases from specifications"

    def _run(self, specification: str, regulatory_context: List[str]) -> Dict[str, Any]:
        print("inside TestCaseGeneratorTool _run")
        print("specification received in tool: ", specification)
        print("regulatory_context received in tool: ", regulatory_context)

        features = self._extract_features(specification)
        all_test_cases = []
        for feature in features:
            # Functional test case
            tc_func = self._create_functional_test_case(feature, regulatory_context)
            all_test_cases.append(tc_func)
            # Security test case if needed
            if self._requires_security_testing(feature):
                tc_sec = self._create_security_test_case(feature, regulatory_context)
                all_test_cases.append(tc_sec)
            # Compliance test cases
            tc_comps = self._create_compliance_test_cases(feature, regulatory_context)
            all_test_cases.extend(tc_comps)

        # Traceability matrix
        traceability = self._create_traceability_matrix(specification, features, all_test_cases)

        return {
            "features": [self._feature_to_dict(f) for f in features],
            "test_cases": [self._testcase_to_dict(tc) for tc in all_test_cases],
            "traceability_matrix": [self._traceability_to_dict(tm) for tm in traceability],
            "summary": {
                "total_features": len(features),
                "total_test_cases": len(all_test_cases),
                "coverage": f"{len([tm for tm in traceability if tm.test_case_ids])}/{len(traceability)} requirements covered"
            }
        }

    def _extract_features(self, specification: str) -> List[Feature]:
        # DEMO LOGIC: Replace with LLM processing as needed
        features = []
        text = specification.lower()
        i = 1
        if "patient data" in text:
            features.append(Feature(
                id=f"FEAT-{i:03d}", name="Patient Data Handling",
                actors=["doctor", "nurse", "patient"], actions=["create", "view", "update"],
                data=["patient record"], business_rules=["HIPAA compliance"], priority="HIGH", complexity="HIGH"
            )); i += 1
        if "authentication" in text or "login" in text:
            features.append(Feature(
                id=f"FEAT-{i:03d}", name="User Authentication",
                actors=["user", "admin"], actions=["login", "logout"],
                data=["credentials"], business_rules=["Session timeout"], priority="HIGH", complexity="MEDIUM"
            )); i += 1
        if "reporting" in text:
            features.append(Feature(
                id=f"FEAT-{i:03d}", name="Report Generation",
                actors=["admin"], actions=["generate", "export"],
                data=["report"], business_rules=["Access log"], priority="MEDIUM", complexity="MEDIUM"
            )); i += 1
        if not features:
            features.append(Feature(
                id=f"FEAT-{i:03d}", name="Core Functionality",
                actors=["user"], actions=["use"], data=["system data"],
                business_rules=[], priority="MEDIUM", complexity="MEDIUM"
            ))
        return features

    def _create_functional_test_case(self, feature: Feature, regulatory_context: List[str]) -> TestCase:
        return TestCase(
            id=str(uuid.uuid4()),
            title=f"Functional Test - {feature.name}",
            feature_id=feature.id,
            description=f"Verify that {feature.name} works as specified.",
            steps=[
                f"Login as {feature.actors[0] if feature.actors else 'user'}",
                f"Navigate to {feature.name}",
                f"Perform {feature.actions[0] if feature.actions else 'action'}",
                "Verify results"
            ],
            expected=[f"{feature.name} executes successfully", "No errors displayed"],
            priority=feature.priority,
            traceability_id=f"REQ-{feature.id}-FUNC"
        )

    def _requires_security_testing(self, feature: Feature) -> bool:
        triggers = ["patient", "authentic", "integrat"]
        return any(t in feature.name.lower() for t in triggers)

    def _create_security_test_case(self, feature: Feature, regulatory_context: List[str]) -> TestCase:
        return TestCase(
            id=str(uuid.uuid4()),
            title=f"Security Test - {feature.name}",
            feature_id=feature.id,
            description=f"Verify security controls for {feature.name}",
            steps=[
                "Attempt unauthorized access",
                "Verify access is denied",
                "Check audit logs"
            ],
            expected=["Access denied", "Security event logged"],
            priority="Critical",
            traceability_id=f"SEC-{feature.id}-SEC"
        )

    def _create_compliance_test_cases(self, feature: Feature, regulatory_context: List[str]) -> List[TestCase]:
        compliance_cases = []
        for regulation in regulatory_context:
            if regulation in HEALTHCARE_REGULATIONS:
                compliance_cases.append(TestCase(
                    id=str(uuid.uuid4()),
                    title=f"{regulation} Compliance - {feature.name}",
                    feature_id=feature.id,
                    description=f"Verify {regulation} compliance for {feature.name}",
                    steps=[
                        f"Review {regulation} requirements",
                        f"Test {feature.name} against requirements",
                        "Document compliance evidence"
                    ],
                    expected=[f"{regulation} requirements met"],
                    priority="Critical",
                    traceability_id=f"COMP-{regulation}-{feature.id}"
                ))
        return compliance_cases

    def _create_traceability_matrix(self, specification: str, features: List[Feature], test_cases: List[TestCase]) -> List[TraceabilityMatrix]:
        # Simple prototype: split specification into (long) sentences as requirements
        requirements = [s.strip() for s in specification.split('.') if len(s.strip()) > 20]
        matrices = []
        for i, req_text in enumerate(requirements):
            req_id = f"REQ-{i+1:03d}"
            feature_ids = [f.id for f in features if any(w in req_text.lower() for w in f.name.lower().split())]
            test_case_ids = [tc.id for tc in test_cases if tc.feature_id in feature_ids]
            matrices.append(TraceabilityMatrix(
                requirement_id=req_id,
                requirement_text=req_text,
                feature_ids=feature_ids,
                test_case_ids=test_case_ids
            ))
        return matrices

    def _feature_to_dict(self, feature: Feature) -> Dict:
        return feature.__dict__

    def _testcase_to_dict(self, tc: TestCase) -> Dict:
        return tc.__dict__

    def _traceability_to_dict(self, tm: TraceabilityMatrix) -> Dict:
        return {
            "requirement_id": tm.requirement_id,
            "requirement_text": tm.requirement_text,
            "feature_ids": tm.feature_ids,
            "test_case_ids": tm.test_case_ids,
            "coverage": bool(tm.test_case_ids)
        }

# Usage: result = tool._run("specification string here...", ["HIPAA", "GDPR"])
```

### Integration Notes

- This version uses the dataclass-based approach throughout, maps requirements to both features and test cases, and supports enhanced traceability and reporting.
- Expand `_extract_features` and other methods to use your LLM pipeline for real extraction if desired.
- Each generated test case, feature, and traceability matrix is returned as a structured dictionary for downstream processing or storage.

This design will give you structured outputs, full traceability, regulatory tag mapping, and a scalable foundation for advanced healthcare test case automation.[1]

[1](https://www.practitest.com/resource-center/article/requirement-traceability-matrix-rtm/)