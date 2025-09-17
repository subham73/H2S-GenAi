from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import uuid
from pydantic import BaseModel, Field

######
class FunctionalAreas(BaseModel):
    modules: List[str] = Field(default_factory=list)
    workflows: List[str] = Field(default_factory=list)
    use_cases: List[str] = Field(default_factory=list)

class SecurityConsiderations(BaseModel):
    data_protection: Optional[str] = ""
    user_authentication: Optional[str] = ""
    authorization: Optional[str] = ""
    access_control: Optional[str] = ""
    logging: Optional[str] = ""
    incident_detection: Optional[str] = ""

class ComplianceRequirements(BaseModel):
    regulations: List[str] = Field(default_factory=list)
    compliance_measures: Dict[str, str] = Field(default_factory=dict)
    auditability: Optional[str] = ""

class DataHandling(BaseModel):
    data_entities: List[str] = Field(default_factory=list)
    data_collection: Optional[str] = ""
    data_storage: Optional[str] = ""
    data_transmission: Optional[str] = ""
    retention_policy: Optional[str] = ""
    backup_policy: Optional[str] = ""
    deletion_policy: Optional[str] = ""

class OtherCriticalAspects(BaseModel):
    interoperability: Optional[str] = ""
    integration: Optional[str] = ""
    performance: Optional[str] = ""
    scalability: Optional[str] = ""
    usability: Optional[str] = ""
    monitoring: Optional[str] = ""

class RequirementAnalysis(BaseModel):
    functional_areas: FunctionalAreas = FunctionalAreas()
    security_considerations: SecurityConsiderations = SecurityConsiderations()
    compliance_requirements: ComplianceRequirements = ComplianceRequirements()
    data_handling: DataHandling = DataHandling()
    other_critical_aspects: OtherCriticalAspects = OtherCriticalAspects()
######

class TestCase(BaseModel):
    id: str = Field(..., description="Unique identifier for the test case")
    title: str = Field(..., description="Title of the test case")
    description: str = Field(..., description="Detailed description of what the test case verifies")
    preconditions: List[str] = Field(default_factory=list, description="Preconditions to be met before running the test")
    steps: List[str] = Field(default_factory=list, description="Step-by-step actions to perform the test")
    expected_results: List[str] = Field(default_factory=list, description="Expected outcomes from the test steps")
    priority: str = Field(..., description="Priority level of the test case, e.g., High, Medium, Low")
    regulatory_tags: Optional[List[str]] = Field(default_factory=list, description="Applicable regulatory standards or tags")
    traceability_id: Optional[str] = Field("", description="Traceability reference to requirements or features")

class ComplianceResult(BaseModel):
    test_case_id: str
    regulation: str
    compliance_status: str
    violations: List[str]
    recommendations: List[str]
    risk_level: str

class QAState(BaseModel):
    requirement: str = ""
    requirement_analysis: Optional[RequirementAnalysis] = None
    regulatory_requirements: List[str] = Field(default_factory=list)
    current_step: str = "orchestration"
    messages: List[BaseMessage] = Field(default_factory=list)
    test_cases: List[TestCase] = Field(default_factory=list)
    compliance_results: List[ComplianceResult] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    workflow_complete: bool = False
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True  # Needed for BaseMessage from langchain_core


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


from datetime import datetime
from uuid import uuid4

sample_qastate = {
    "requirement": "The system shall allow patients to book, reschedule, and cancel appointments with automated reminders.",
    "requirement_analysis": {
        "functional_areas": {
            "modules": ["Appointment Management", "Notification Service"],
            "workflows": ["Booking Workflow", "Cancellation Workflow"],
            "use_cases": ["Book appointment", "Cancel appointment", "Reschedule appointment"]
        },
        "security_considerations": {
            "data_protection": "Encrypt patient data at rest and in transit",
            "user_authentication": "OAuth2 with MFA",
            "authorization": "Role-based access control",
            "access_control": "Granular permissions per module",
            "logging": "Audit logs for all booking changes",
            "incident_detection": "Automated anomaly detection on booking patterns"
        },
        "compliance_requirements": {
            "regulations": ["HIPAA", "FDA"],
            "compliance_measures": {
                "HIPAA": "Ensure PHI is encrypted and access logged",
                "FDA": "Maintain audit trails for all scheduling changes"
            },
            "auditability": "All actions timestamped and traceable"
        },
        "data_handling": {
            "data_entities": ["Patient", "Appointment", "Doctor", "Room"],
            "data_collection": "Collected via secure web forms",
            "data_storage": "Encrypted database with daily backups",
            "data_transmission": "TLS 1.3 for all API calls",
            "retention_policy": "Retain appointment data for 7 years",
            "backup_policy": "Daily incremental backups, weekly full backups",
            "deletion_policy": "Secure deletion after retention period"
        },
        "other_critical_aspects": {
            "interoperability": "HL7/FHIR integration with EMR",
            "integration": "Integrates with SMS and email gateways",
            "performance": "Under 2s response time for booking actions",
            "scalability": "Supports up to 10,000 concurrent users",
            "usability": "Mobile-first responsive design",
            "monitoring": "Real-time health checks and alerting"
        }
    },
    "regulatory_requirements": ["HIPAA", "FDA"],
    "current_step": "compliance_check",
    "messages": [],  # Could contain LangChain BaseMessage objects
    "test_cases": [
        {
            "id": "TC-001",
            "title": "Book Appointment - Happy Path",
            "description": "Verify that a patient can successfully book an appointment.",
            "preconditions": ["User is logged in", "Doctor is available"],
            "steps": [
                "Navigate to booking page",
                "Select doctor and time slot",
                "Confirm booking"
            ],
            "expected_results": [
                "Booking confirmation displayed",
                "Reminder email sent"
            ],
            "priority": "High",
            "regulatory_tags": ["HIPAA"],
            "traceability_id": "REQ-001"
        }
    ],
    "compliance_results": [
        {
            "test_case_id": "TC-001",
            "regulation": "HIPAA",
            "compliance_status": "Compliant",
            "violations": [],
            "recommendations": [],
            "risk_level": "Low"
        }
    ],
    "errors": [],
    "workflow_complete": True,
    "workflow_id": str(uuid4()),
    "created_at": datetime.now().isoformat()
}