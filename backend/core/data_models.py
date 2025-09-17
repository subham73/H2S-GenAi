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

@dataclass
class ComplianceResult:
    test_case_id: str
    regulation: str
    compliance_status: str
    violations: List[str]
    recommendations: List[str]
    risk_level: str

@dataclass
class QAState: # TODO : change it to pydantic model later
    requirement: str = "" 
    requirement_analysis: Optional[RequirementAnalysis] = None
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