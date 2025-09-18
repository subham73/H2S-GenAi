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

sample_test_compliance = {
  "test_cases": [
    {
      "id": "TC-001",
      "title": "Patient Registration with Consent",
      "description": "Verify that new patient registration requires capturing explicit consent for storing personal and medical data.",
      "preconditions": ["System online", "Admin logged in"],
      "steps": [
        "Navigate to patient registration page",
        "Enter demographic and medical details",
        "Submit registration form"
      ],
      "expected_results": [
        "System prompts for explicit patient consent before saving",
        "Consent record stored with timestamp"
      ],
      "priority": "High",
      "regulatory_tags": ["GDPR", "HIPAA"],
      "traceability_id": "REQ-PR-001"
    },
    {
      "id": "TC-002",
      "title": "Vaccine Stock Audit Trail",
      "description": "Ensure all stock movements (inbound, outbound, wastage) are logged with user identity, timestamp, and reason.",
      "preconditions": ["System has vaccine stock records"],
      "steps": [
        "Perform stock entry",
        "Perform vaccine issuance",
        "Perform vaccine wastage disposal"
      ],
      "expected_results": [
        "Each transaction has unique ID",
        "Logs include user identity, timestamp, and justification"
      ],
      "priority": "High",
      "regulatory_tags": ["WHO", "ISO 27001"],
      "traceability_id": "REQ-STK-002"
    },
    {
      "id": "TC-003",
      "title": "Cold Chain Temperature Monitoring",
      "description": "Verify system alerts when vaccine storage temperature exceeds 2–8°C range.",
      "preconditions": ["Cold chain monitoring devices connected"],
      "steps": [
        "Simulate rise in temperature to 10°C",
        "Check if alert notification is generated"
      ],
      "expected_results": [
        "System generates high-priority alert",
        "Alert logged and sent to responsible staff"
      ],
      "priority": "High",
      "regulatory_tags": ["WHO"],
      "traceability_id": "REQ-CC-003"
    },
    {
      "id": "TC-004",
      "title": "Role-Based Access for Medical Staff",
      "description": "Ensure doctors can view and update patient vaccination records, but receptionists can only view, not update.",
      "preconditions": ["Users created with roles: Doctor, Receptionist"],
      "steps": [
        "Login as Doctor and try updating vaccination record",
        "Login as Receptionist and attempt the same update"
      ],
      "expected_results": [
        "Doctor update succeeds",
        "Receptionist update is denied with an error message"
      ],
      "priority": "Medium",
      "regulatory_tags": ["HIPAA", "ISO 27001"],
      "traceability_id": "REQ-SEC-004"
    },
    {
      "id": "TC-005",
      "title": "Data Retention & Deletion Policy",
      "description": "Verify that vaccination records older than 10 years are anonymized or deleted according to retention policy.",
      "preconditions": ["Database seeded with >10 year old records"],
      "steps": [
        "Run retention policy job",
        "Inspect patient data older than 10 years"
      ],
      "expected_results": [
        "Records older than 10 years are anonymized or deleted",
        "Audit log entry created for each deletion"
      ],
      "priority": "Medium",
      "regulatory_tags": ["GDPR", "HIPAA"],
      "traceability_id": "REQ-DH-005"
    }
  ],
  "compliance_results": [
    {
      "test_case_id": "TC-001",
      "regulation": "GDPR",
      "compliance_status": "Compliant",
      "violations": [],
      "recommendations": [],
      "risk_level": "Low"
    },
    {
      "test_case_id": "TC-001",
      "regulation": "HIPAA",
      "compliance_status": "Partial",
      "violations": ["Consent form not encrypted at rest"],
      "recommendations": ["Enable encryption for stored consent forms"],
      "risk_level": "Medium"
    },
    {
      "test_case_id": "TC-002",
      "regulation": "WHO",
      "compliance_status": "Compliant",
      "violations": [],
      "recommendations": [],
      "risk_level": "Low"
    },
    {
      "test_case_id": "TC-002",
      "regulation": "ISO 27001",
      "compliance_status": "Non-Compliant",
      "violations": ["Audit logs not tamper-proof"],
      "recommendations": ["Implement immutable logging with blockchain or WORM storage"],
      "risk_level": "High"
    },
    {
      "test_case_id": "TC-003",
      "regulation": "WHO",
      "compliance_status": "Compliant",
      "violations": [],
      "recommendations": [],
      "risk_level": "Low"
    },
    {
      "test_case_id": "TC-004",
      "regulation": "HIPAA",
      "compliance_status": "Compliant",
      "violations": [],
      "recommendations": [],
      "risk_level": "Low"
    },
    {
      "test_case_id": "TC-004",
      "regulation": "ISO 27001",
      "compliance_status": "Partial",
      "violations": ["Receptionist access logs missing"],
      "recommendations": ["Enable activity logging for all roles"],
      "risk_level": "Medium"
    },
    {
      "test_case_id": "TC-005",
      "regulation": "GDPR",
      "compliance_status": "Non-Compliant",
      "violations": ["Records older than 10 years remain accessible with patient identifiers"],
      "recommendations": ["Implement automatic anonymization for records beyond retention period"],
      "risk_level": "High"
    },
    {
      "test_case_id": "TC-005",
      "regulation": "HIPAA",
      "compliance_status": "Partial",
      "violations": ["Audit log of deleted records not retained properly"],
      "recommendations": ["Ensure deletion logs are immutable and retained for minimum 6 years"],
      "risk_level": "Medium"
    }
  ]
}
