import asyncio
from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime
import json
import uuid

from langgraph.graph import StateGraph, END
# from langgraph.prebuilt import ToolExecutor
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


# Data Models
@dataclass
class TestCase:
    id: str
    title: str
    description: str
    preconditions: List[str]
    steps: List[Dict[str, str]]
    expected_results: List[str]
    priority: str
    regulatory_tags: List[str]
    traceability_id: str
    created_at: datetime
    compliance_status: Optional[str] = None

@dataclass
class ComplianceResult:
    test_case_id: str
    regulation: str
    compliance_status: str
    violations: List[str]
    recommendations: List[str]
    risk_level: str

@dataclass
class QAState:
    """Central state for the QA automation workflow"""
    # Input data
    specification: str = ""
    regulatory_requirements: List[str] = field(default_factory=list)
    
    # Processing state
    current_step: str = "orchestration"
    messages: List[BaseMessage] = field(default_factory=list)
    
    # Generated artifacts
    test_cases: List[TestCase] = field(default_factory=list)
    compliance_results: List[ComplianceResult] = field(default_factory=list)
    
    # Workflow control
    errors: List[str] = field(default_factory=list)
    workflow_complete: bool = False
    
    # Traceability
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)


# Compliance Framework Definitions
HEALTHCARE_REGULATIONS = {
    "HIPAA": {
        "description": "Health Insurance Portability and Accountability Act",
        "key_requirements": [
            "Patient data encryption",
            "Access controls and audit logs", 
            "Data breach notification procedures",
            "Business associate agreements",
            "Minimum necessary standard"
        ]
    },
    "FDA_510K": {
        "description": "FDA 510(k) Medical Device Requirements",
        "key_requirements": [
            "Predicate device comparison",
            "Risk analysis documentation",
            "Clinical validation",
            "Software lifecycle processes",
            "Cybersecurity documentation"
        ]
    },
    "IEC_62304": {
        "description": "Medical Device Software Lifecycle",
        "key_requirements": [
            "Software safety classification",
            "Risk management process",
            "Software architecture documentation",
            "Verification and validation",
            "Problem resolution process"
        ]
    },
    "GDPR": {
        "description": "General Data Protection Regulation",
        "key_requirements": [
            "Data subject consent",
            "Right to be forgotten",
            "Data portability",
            "Privacy by design",
            "Data protection impact assessment"
        ]
    }
}


# Agent Tools
class TestCaseGeneratorTool(BaseTool):
    name: str = "test_case_generator"
    description: str = "Generates comprehensive test cases from specifications"
    
    def _run(self, specification: str, regulatory_context: List[str]) -> List[Dict]:
        """Generate test cases based on specification and regulatory context"""
        print("comming to testcase generatortool")
        # Parse specification to identify key features
        features = self._extract_features(specification)
        test_cases = []
        
        for feature in features:
            # Generate functional test cases
            functional_tc = self._create_functional_test_case(feature, regulatory_context)
            test_cases.append(functional_tc)
            
            # Generate security test cases if applicable
            if self._requires_security_testing(feature, regulatory_context):
                security_tc = self._create_security_test_case(feature, regulatory_context)
                test_cases.append(security_tc)
            
            # Generate compliance-specific test cases
            compliance_tcs = self._create_compliance_test_cases(feature, regulatory_context)
            test_cases.extend(compliance_tcs)
        
        return test_cases
    
    def _extract_features(self, specification: str) -> List[str]:
        """Extract testable features from specification"""
        # Simplified feature extraction - in real implementation would use NLP
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
        """Create functional test case for a feature"""
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
        """Determine if feature requires security testing"""
        security_triggers = ["patient_data", "authentication", "integration"]
        return any(trigger in feature for trigger in security_triggers)
    
    def _create_security_test_case(self, feature: str, regulatory_context: List[str]) -> Dict:
        """Create security test case for a feature"""
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
        """Create compliance-specific test cases"""
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


class ComplianceCheckerTool(BaseTool):
    name: str = "compliance_checker"
    description: str = "Validates test cases against regulatory requirements"
    
    def _run(self, test_cases: List[Dict], regulations: List[str]) -> List[Dict]:
        """Check test cases for compliance with specified regulations"""
        print("comming to compliance checker Tool ")
        compliance_results = []
        
        for test_case in test_cases:
            for regulation in regulations:
                result = self._check_regulation_compliance(test_case, regulation)
                compliance_results.append(result)
        
        return compliance_results
    
    def _check_regulation_compliance(self, test_case: Dict, regulation: str) -> Dict:
        """Check a single test case against a specific regulation"""
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
        
        # Check for regulation-specific requirements
        if regulation == "HIPAA":
            violations, recommendations, risk_level = self._check_hipaa_compliance(test_case)
        elif regulation == "FDA_510K":
            violations, recommendations, risk_level = self._check_fda_510k_compliance(test_case)
        elif regulation == "IEC_62304":
            violations, recommendations, risk_level = self._check_iec_62304_compliance(test_case)
        elif regulation == "GDPR":
            violations, recommendations, risk_level = self._check_gdpr_compliance(test_case)
        
        # Determine overall compliance status
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
        """Check HIPAA compliance"""
        violations = []
        recommendations = []
        risk_level = "Low"
        
        # Check for PHI handling
        if "patient" in test_case["description"].lower():
            if not any("encryption" in step.get("action", "").lower() for step in test_case["steps"]):
                violations.append("No encryption verification for PHI handling")
                risk_level = "High"
            
            if not any("audit" in step.get("action", "").lower() for step in test_case["steps"]):
                recommendations.append("Add audit log verification step")
        
        return violations, recommendations, risk_level
    
    def _check_fda_510k_compliance(self, test_case: Dict) -> tuple:
        """Check FDA 510(k) compliance"""
        violations = []
        recommendations = []
        risk_level = "Low"
        
        # Check for risk analysis documentation
        if test_case["priority"] == "Critical":
            if not test_case.get("traceability_id", "").startswith("RISK"):
                recommendations.append("Link to risk analysis documentation")
        
        return violations, recommendations, risk_level
    
    def _check_iec_62304_compliance(self, test_case: Dict) -> tuple:
        """Check IEC 62304 compliance"""
        violations = []
        recommendations = []
        risk_level = "Low"
        
        # Check software safety classification
        if not test_case.get("regulatory_tags"):
            violations.append("No software safety classification specified")
            risk_level = "Medium"
        
        return violations, recommendations, risk_level
    
    def _check_gdpr_compliance(self, test_case: Dict) -> tuple:
        """Check GDPR compliance"""
        violations = []
        recommendations = []
        risk_level = "Low"
        
        # Check for data subject rights
        if "data" in test_case["description"].lower():
            if not any("consent" in step.get("action", "").lower() for step in test_case["steps"]):
                recommendations.append("Add consent verification step")
        
        return violations, recommendations, risk_level


# Agent Implementations
class OrchestratorAgent:
    """Orchestrates the QA workflow and coordinates between agents"""
    
    def __init__(self, llm):
        self.llm = llm
    
    async def run(self, state: QAState) -> QAState:
        """Orchestrate the QA automation workflow"""
        print("comming to OrchestrattorAgent")
        state.messages.append(HumanMessage(content="Starting QA automation workflow"))
        state.current_step = "orchestration"
        
        # Analyze the specification and determine workflow
        analysis = await self._analyze_specification(state.specification)
        
        # Extract regulatory requirements if not provided
        if not state.regulatory_requirements:
            state.regulatory_requirements = self._extract_regulatory_requirements(state.specification)
        
        # Set up workflow plan
        workflow_plan = self._create_workflow_plan(analysis, state.regulatory_requirements)
        
        state.messages.append(AIMessage(content=f"Workflow plan created: {workflow_plan}"))
        
        # Determine next step
        state.current_step = "test_generation"
        
        return state
    
    async def _analyze_specification(self, specification: str) -> Dict:
        """Analyze specification to understand requirements"""
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
        
        return {
            "functional_areas": ["patient_management", "data_processing", "reporting"],
            "data_requirements": ["PHI_handling", "audit_trails"],
            "integration_points": ["EHR_systems", "lab_interfaces"],
            "security_needs": ["authentication", "encryption", "access_control"]
        }
    
    def _extract_regulatory_requirements(self, specification: str) -> List[str]:
        """Extract applicable regulatory requirements from specification"""
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
        
        # Default to HIPAA for healthcare software
        if not regulations:
            regulations.append("HIPAA")
        
        return regulations
    
    def _create_workflow_plan(self, analysis: Dict, regulations: List[str]) -> Dict:
        """Create execution plan for the workflow"""
        return {
            "steps": ["test_generation", "compliance_check", "finalization"],
            "estimated_test_cases": len(analysis["functional_areas"]) * 3,
            "compliance_checks": len(regulations),
            "priority": "high" if "Critical" in str(analysis) else "medium"
        }


class TestCaseGeneratorAgent:
    """Generates comprehensive test cases from specifications"""
    
    def __init__(self, llm):
        self.llm = llm
        self.tool = TestCaseGeneratorTool()
    
    async def run(self, state: QAState) -> QAState:
        """Generate test cases based on specification and regulatory requirements"""
        print("comming to testcase Generator Agent")
        state.current_step = "test_generation"
        state.messages.append(HumanMessage(content="Generating test cases"))
        
        # Generate test cases using the tool
        test_case_dicts = self.tool.run(
            specification=state.specification,
            regulatory_context=state.regulatory_requirements
        )
        
        # Convert dictionaries to TestCase objects
        test_cases = []
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
            test_cases.append(test_case)
        
        state.test_cases = test_cases
        state.messages.append(AIMessage(content=f"Generated {len(test_cases)} test cases"))
        
        # Move to next step
        state.current_step = "compliance_check"
        
        return state


class ComplianceCheckAgent:
    """Validates test cases against regulatory requirements"""
    
    def __init__(self, llm):
        self.llm = llm
        self.tool = ComplianceCheckerTool()
    
    async def run(self, state: QAState) -> QAState:
        """Check test cases for compliance with regulatory requirements"""
        print("comming to compliance checking agent")
        state.current_step = "compliance_check"
        state.messages.append(HumanMessage(content="Checking compliance"))
        
        # Convert TestCase objects to dictionaries for the tool
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
        
        # Run compliance check
        compliance_result_dicts = self.tool.run(
            test_cases=test_case_dicts,
            regulations=state.regulatory_requirements
        )
        
        # Convert to ComplianceResult objects
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
            compliance_results.append(compliance_result)
        
        state.compliance_results = compliance_results
        
        # Update test cases with compliance status
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
        
        # Move to finalization
        state.current_step = "finalization"
        
        return state


# Workflow Definition
def create_qa_workflow():
    """Create the LangGraph workflow for QA automation"""
    print("inside qa workingflow")
    
    # Initialize LLM (replace with your preferred LLM)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Initialize agents
    orchestrator = OrchestratorAgent(llm)
    test_generator = TestCaseGeneratorAgent(llm)
    compliance_checker = ComplianceCheckAgent(llm)
    
    # Define workflow graph
    workflow = StateGraph(QAState)
    
    # Add nodes
    workflow.add_node("orchestrator", orchestrator.run)
    workflow.add_node("test_generator", test_generator.run)
    workflow.add_node("compliance_checker", compliance_checker.run)
    workflow.add_node("finalize", finalize_workflow)
    
    # Define edges
    workflow.set_entry_point("orchestrator")
    workflow.add_edge("orchestrator", "test_generator")
    workflow.add_edge("test_generator", "compliance_checker")
    workflow.add_edge("compliance_checker", "finalize")
    workflow.add_edge("finalize", END)
    
    return workflow.compile()


def finalize_workflow(state: QAState) -> QAState:
    """Finalize the workflow and prepare outputs"""
    print("Inside Finalizing workflow...")
    state.current_step = "complete"
    state.workflow_complete = True
    
    # Generate summary
    total_test_cases = len(state.test_cases)
    compliant_cases = len([tc for tc in state.test_cases if tc.compliance_status == "Compliant"])
    total_violations = sum(len(cr.violations) for cr in state.compliance_results)
    
    summary_message = f"""
    QA Automation Workflow Complete:
    - Total Test Cases Generated: {total_test_cases}
    - Compliant Test Cases: {compliant_cases}
    - Total Compliance Violations: {total_violations}
    - Regulatory Frameworks Checked: {len(state.regulatory_requirements)}
    """
    
    state.messages.append(AIMessage(content=summary_message))
    
    return state


# Utility Functions
def generate_traceability_matrix(state: QAState) -> Dict:
    """Generate traceability matrix linking requirements to test cases"""
    print("inside generate tracebility matrix")
    matrix = {}
    
    for test_case in state.test_cases:
        req_id = test_case.traceability_id
        if req_id not in matrix:
            matrix[req_id] = []
        
        matrix[req_id].append({
            "test_case_id": test_case.id,
            "test_case_title": test_case.title,
            "priority": test_case.priority,
            "compliance_status": test_case.compliance_status,
            "regulatory_tags": test_case.regulatory_tags
        })
    
    return matrix


def export_test_cases_to_json(state: QAState) -> str:
    """Export test cases to JSON format"""
    print("inside export test cases to json")
    export_data = {
        "workflow_id": state.workflow_id,
        "created_at": state.created_at.isoformat(),
        "regulatory_requirements": state.regulatory_requirements,
        "test_cases": [],
        "compliance_results": []
    }
    
    # Export test cases
    for tc in state.test_cases:
        tc_data = {
            "id": tc.id,
            "title": tc.title,
            "description": tc.description,
            "preconditions": tc.preconditions,
            "steps": tc.steps,
            "expected_results": tc.expected_results,
            "priority": tc.priority,
            "regulatory_tags": tc.regulatory_tags,
            "traceability_id": tc.traceability_id,
            "compliance_status": tc.compliance_status,
            "created_at": tc.created_at.isoformat()
        }
        export_data["test_cases"].append(tc_data)
    
    # Export compliance results
    for cr in state.compliance_results:
        cr_data = {
            "test_case_id": cr.test_case_id,
            "regulation": cr.regulation,
            "compliance_status": cr.compliance_status,
            "violations": cr.violations,
            "recommendations": cr.recommendations,
            "risk_level": cr.risk_level
        }
        export_data["compliance_results"].append(cr_data)
    
    return json.dumps(export_data, indent=2)


# Example Usage
async def main():
    """Example usage of the QA automation system"""
    
    # Sample healthcare software specification
    print("in main bebe")
    specification = """
    Healthcare Patient Management System:
    
    The system shall provide secure patient data management capabilities including:
    - Patient registration and demographic data storage
    - Medical history tracking with audit trails
    - Integration with external laboratory systems
    - HIPAA-compliant data encryption and access controls
    - Role-based authentication for healthcare providers
    - Automated report generation for regulatory compliance
    - Data backup and disaster recovery procedures
    
    The system must comply with HIPAA, FDA 510(k) requirements for medical devices,
    and implement IEC 62304 software lifecycle processes.
    """
    
    # Initialize workflow state
    initial_state = QAState(
        specification=specification,
        regulatory_requirements=["HIPAA", "FDA_510K", "IEC_62304"]
    )
    
    # Create and run workflow
    workflow = create_qa_workflow()
    
    print("Starting Healthcare QA Automation Workflow...")
    
    try:
        # Execute workflow
        final_state = await workflow.ainvoke(initial_state)
        
        # Display results
        print(f"\nWorkflow completed successfully!")
        print(f"Generated {len(final_state.test_cases)} test cases")
        print(f"Performed {len(final_state.compliance_results)} compliance checks")
        
        # Show sample test cases
        print("\nSample Test Cases:")
        for i, tc in enumerate(final_state.test_cases[:3]):  # Show first 3
            print(f"\n{i+1}. {tc.title}")
            print(f"   Priority: {tc.priority}")
            print(f"   Compliance: {tc.compliance_status}")
            print(f"   Regulatory Tags: {', '.join(tc.regulatory_tags)}")
        
        # Show compliance summary
        violations = [cr for cr in final_state.compliance_results if cr.violations]
        if violations:
            print(f"\nCompliance Issues Found: {len(violations)}")
            for violation in violations[:3]:  # Show first 3
                print(f"- {violation.regulation}: {', '.join(violation.violations)}")
        
        # Generate traceability matrix
        traceability = generate_traceability_matrix(final_state)
        print(f"\nTraceability Matrix: {len(traceability)} requirements traced")
        
        # Export to JSON
        json_export = export_test_cases_to_json(final_state)
        print(f"\nExport completed: {len(json_export)} characters")
        
    except Exception as e:
        print(f"Workflow failed: {str(e)}")


if __name__ == "__main__":
    # Note: You'll need to set up your OpenAI API key
    # export OPENAI_API_KEY="your-api-key-here"
    asyncio.run(main())