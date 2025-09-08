from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import uuid


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
    specification: str = "" # TODO : change name of it to somehting else
    regulatory_requirements: List[str] = field(default_factory=list)
    current_step: str = "orchestration"
    messages: List[BaseMessage] = field(default_factory=list)
    test_cases: List[TestCase] = field(default_factory=list)
    compliance_results: List[ComplianceResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    workflow_complete: bool = False
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)


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