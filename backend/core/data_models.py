from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import uuid
from pydantic import BaseModel, Field, model_validator

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
    compliance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score between 0 and 1")
    compliance_status: Optional[str] = Field(
        None, description="Compliant | Partial | Non-Compliant | Needs human review"
    )
    recommendations: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    violations: List[str] = Field(default_factory=list, description="Detected compliance risks")
    regulatory_citations: List[str] = Field(default_factory=list, description="Relevant regulatory references")

    @model_validator(mode="after")
    def normalize_fields(self) -> "ComplianceResult":
      if self.compliance_score is None:
          self.compliance_score = 0.0
      return self 

    @model_validator(mode="after")
    def infer_status_from_score(self) -> "ComplianceResult":
      if self.compliance_score is not None and self.compliance_status is None:
          if self.compliance_score >= 0.85:
              self.compliance_status = "Compliant"
          elif self.compliance_score >= 0.40:
              self.compliance_status = "Partial"
          else:
              self.compliance_status = "Non-Compliant"
      return self



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
      "compliance_score": 0.95,
      "compliance_status": "Compliant",
      "recommendations": [],
      "violations": [],
      "regulatory_citations": []
    },
    {
      "test_case_id": "TC-001",
      "regulation": "HIPAA",
      "compliance_score": 0.65,
      "compliance_status": "Partial",
      "recommendations": ["Enable encryption for stored consent forms"],
      "violations": ["Consent form not encrypted at rest"],
      "regulatory_citations": []
    },
    {
      "test_case_id": "TC-002",
      "regulation": "WHO",
      "compliance_score": 0.90,
      "compliance_status": "Compliant",
      "recommendations": [],
      "violations": [],
      "regulatory_citations": []
    },
    {
      "test_case_id": "TC-002",
      "regulation": "ISO 27001",
      "compliance_score": 0.30,
      "compliance_status": "Non-Compliant",
      "recommendations": ["Implement immutable logging with blockchain or WORM storage"],
      "violations": ["Audit logs not tamper-proof"],
      "regulatory_citations": []
    },
    {
      "test_case_id": "TC-003",
      "regulation": "WHO",
      "compliance_score": 0.92,
      "compliance_status": "Compliant",
      "recommendations": [],
      "violations": [],
      "regulatory_citations": []
    },
    {
      "test_case_id": "TC-004",
      "regulation": "HIPAA",
      "compliance_score": 0.88,
      "compliance_status": "Compliant",
      "recommendations": [],
      "violations": [],
      "regulatory_citations": []
    },
    {
      "test_case_id": "TC-004",
      "regulation": "ISO 27001",
      "compliance_score": 0.60,
      "compliance_status": "Partial",
      "recommendations": ["Enable activity logging for all roles"],
      "violations": ["Receptionist access logs missing"],
      "regulatory_citations": []
    },
    {
      "test_case_id": "TC-005",
      "regulation": "GDPR",
      "compliance_score": 0.25,
      "compliance_status": "Non-Compliant",
      "recommendations": ["Implement automatic anonymization for records beyond retention period"],
      "violations": ["Records older than 10 years remain accessible with patient identifiers"],
      "regulatory_citations": []
    },
    {
      "test_case_id": "TC-005",
      "regulation": "HIPAA",
      "compliance_score": 0.55,
      "compliance_status": "Partial",
      "recommendations": ["Ensure deletion logs are immutable and retained for minimum 6 years"],
      "violations": ["Audit log of deleted records not retained properly"],
      "regulatory_citations": []
    }
  ]
}

completeQA = {
  "requirement": "The system shall provide patients and healthcare providers the ability to book, reschedule, and cancel appointments. Automated reminders must be sent via SMS/email to patients and staff prior to scheduled appointments. The schedule must reflect real-time availability and prevent double-booking of resources (doctors, rooms, equipment).",
  "requirement_analysis": {
    "functional_areas": {
      "modules": [
        "Appointment Management",
        "Scheduling Engine",
        "Notification System",
        "Resource Management"
      ],
      "workflows": [
        "Appointment Booking (Patient initiated)",
        "Appointment Booking (Provider initiated)",
        "Appointment Rescheduling (Patient initiated)",
        "Appointment Rescheduling (Provider initiated)",
        "Appointment Cancellation (Patient initiated)",
        "Appointment Cancellation (Provider initiated)",
        "Automated Reminder Generation and Delivery",
        "Real-time Availability Update"
      ],
      "use_cases": [
        "Book an Appointment as a Patient",
        "Book an Appointment as a Healthcare Provider",
        "Reschedule an Appointment as a Patient",
        "Reschedule an Appointment as a Healthcare Provider",
        "Cancel an Appointment as a Patient",
        "Cancel an Appointment as a Healthcare Provider",
        "Receive Appointment Reminder (Patient)",
        "Receive Appointment Reminder (Staff)",
        "View Real-time Resource Availability",
        "System Prevents Double-Booking"
      ]
    },
    "security_considerations": {
      "data_protection": "All patient and provider data, including appointment details, must be encrypted at rest and in transit. Measures to prevent unauthorized access, modification, or disclosure of sensitive health information (PHI) are critical.",
      "user_authentication": "Strong authentication mechanisms (e.g., multi-factor authentication) for both patients and healthcare providers to ensure only authorized users can access the system.",
      "authorization": "Role-based access control (RBAC) to define and enforce permissions based on user roles (e.g., patient, doctor, administrator, scheduler). Patients can only manage their own appointments, while providers can manage their own and potentially others' schedules based on their role.",
      "access_control": "Granular access controls to ensure that users can only view or modify data relevant to their role and specific permissions. For instance, a patient can only see their own appointments, while a doctor can see their own schedule and patient details for their appointments.",
      "logging": "Comprehensive logging of all user activities (e.g., appointment booking, rescheduling, cancellation, data access) and system events (e.g., reminder delivery, system errors) for audit trails and incident investigation.",
      "incident_detection": "Mechanisms to detect and alert on suspicious activities, unauthorized access attempts, data breaches, or system anomalies. This includes monitoring logs and system behavior for deviations from normal patterns."
    },
    "compliance_requirements": {
      "regulations": [
        "HIPAA",
        "GDPR",
        "PIPEDA (if applicable in Canada)",
        "CCPA (if applicable in California)"
      ],
      "compliance_measures": {
        "HIPAA": "Implement technical safeguards (encryption, access controls, audit logs), administrative safeguards (security policies, training), and physical safeguards to protect Protected Health Information (PHI) related to appointments and patient identities. Ensure business associate agreements (BAAs) are in place with any third-party services handling PHI (e.g., SMS/email providers).",
        "GDPR": "Ensure explicit consent for data processing, provide data subjects with rights (access, rectification, erasure, portability), implement data minimization, privacy by design, and conduct Data Protection Impact Assessments (DPIAs). Securely process personal data, including contact information for reminders, and ensure data is stored within compliant jurisdictions or with appropriate transfer mechanisms."
      },
      "auditability": "The system must maintain immutable audit trails for all appointment-related actions (creation, modification, cancellation), user logins, and data access. These logs should include timestamps, user identities, and details of the action performed, enabling reconstruction of events for compliance audits and investigations."
    },
    "data_handling": {
      "data_entities": [
        "Patient Records (Name, Contact Info, Appointment History)",
        "Healthcare Provider Records (Name, Specialization, Schedule, Contact Info)",
        "Appointment Records (Date, Time, Duration, Service Type, Patient ID, Provider ID, Resource IDs, Status)",
        "Resource Records (Room, Equipment, Availability)",
        "Notification Logs (Recipient, Message Content, Delivery Status, Timestamp)"
      ],
      "data_collection": "Data will be collected through secure web forms or API integrations when patients or providers book, reschedule, or cancel appointments. Patient contact information for reminders will be collected during the booking process.",
      "data_storage": "All data will be stored in secure, encrypted databases. Patient and provider data will be logically separated or pseudonymized where possible. Storage infrastructure must comply with relevant healthcare data regulations.",
      "data_transmission": "All data transmitted between the client (patient/provider interface) and the server, and between system components, must be encrypted using industry-standard protocols (e.g., TLS 1.2+). SMS and email reminders should be sent via secure, compliant third-party services.",
      "retention_policy": "Appointment and patient data will be retained for a period compliant with legal and regulatory requirements (e.g., HIPAA, state medical record retention laws), typically several years after the last patient interaction. Specific retention periods will be defined per data type.",
      "backup_policy": "Regular, automated backups of all critical data (patient, provider, appointment, resource schedules) will be performed. Backups will be encrypted, stored off-site, and regularly tested for restorability to ensure business continuity and data integrity.",
      "deletion_policy": "Data deletion will adhere to regulatory requirements and user requests (e.g., GDPR 'right to be forgotten'). Data marked for deletion will be securely purged from primary storage and backups after the defined retention period, ensuring irretrievability."
    },
    "other_critical_aspects": {
      "interoperability": "Potential integration with existing Electronic Health Record (EHR) or Practice Management Systems (PMS) to synchronize patient demographics, provider schedules, and potentially appointment types. Adherence to standards like HL7 FHIR for data exchange.",
      "integration": "Integration with SMS gateway providers for text message reminders, email service providers for email reminders, and potentially calendar systems (e.g., Google Calendar, Outlook Calendar) for provider schedule synchronization.",
      "performance": "The system must provide real-time availability updates and process booking, rescheduling, and cancellation requests with minimal latency to ensure a smooth user experience and prevent double-booking. The notification system must reliably send reminders in a timely manner.",
      "scalability": "The system architecture must be scalable to handle a growing number of patients, providers, appointments, and concurrent users without degradation in performance. This includes scaling database, application, and notification services.",
      "usability": "Intuitive and user-friendly interfaces for both patients (for booking/managing appointments) and healthcare providers/staff (for managing schedules, resources, and patient appointments). Clear navigation, accessible design, and efficient workflows are essential.",
      "monitoring": "Continuous monitoring of system health, performance metrics (e.g., response times, error rates), resource utilization, and security events. Alerts should be configured for critical issues, and dashboards should provide real-time insights into system operations and reminder delivery status."
    }
  },
  "regulatory_requirements": [
    "iso",
    "fda"
  ],
  "current_step": "compliance_check",
  "messages": [
  ],
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
      "compliance_score": 0.95,
      "compliance_status": "Compliant",
      "recommendations": [],
      "violations": [],
      "regulatory_citations": []
    },
    {
      "test_case_id": "TC-001",
      "regulation": "HIPAA",
      "compliance_score": 0.65,
      "compliance_status": "Partial",
      "recommendations": ["Enable encryption for stored consent forms"],
      "violations": ["Consent form not encrypted at rest"],
      "regulatory_citations": []
    },
    {
      "test_case_id": "TC-002",
      "regulation": "WHO",
      "compliance_score": 0.90,
      "compliance_status": "Compliant",
      "recommendations": [],
      "violations": [],
      "regulatory_citations": []
    },
    {
      "test_case_id": "TC-002",
      "regulation": "ISO 27001",
      "compliance_score": 0.30,
      "compliance_status": "Non-Compliant",
      "recommendations": ["Implement immutable logging with blockchain or WORM storage"],
      "violations": ["Audit logs not tamper-proof"],
      "regulatory_citations": []
    },
    {
      "test_case_id": "TC-003",
      "regulation": "WHO",
      "compliance_score": 0.92,
      "compliance_status": "Compliant",
      "recommendations": [],
      "violations": [],
      "regulatory_citations": []
    },
    {
      "test_case_id": "TC-004",
      "regulation": "HIPAA",
      "compliance_score": 0.88,
      "compliance_status": "Compliant",
      "recommendations": [],
      "violations": [],
      "regulatory_citations": []
    },
    {
      "test_case_id": "TC-004",
      "regulation": "ISO 27001",
      "compliance_score": 0.60,
      "compliance_status": "Partial",
      "recommendations": ["Enable activity logging for all roles"],
      "violations": ["Receptionist access logs missing"],
      "regulatory_citations": []
    },
    {
      "test_case_id": "TC-005",
      "regulation": "GDPR",
      "compliance_score": 0.25,
      "compliance_status": "Non-Compliant",
      "recommendations": ["Implement automatic anonymization for records beyond retention period"],
      "violations": ["Records older than 10 years remain accessible with patient identifiers"],
      "regulatory_citations": []
    },
    {
      "test_case_id": "TC-005",
      "regulation": "HIPAA",
      "compliance_score": 0.55,
      "compliance_status": "Partial",
      "recommendations": ["Ensure deletion logs are immutable and retained for minimum 6 years"],
      "violations": ["Audit log of deleted records not retained properly"],
      "regulatory_citations": []
    }
  ],
  "errors": [],
  "workflow_complete": False,
  "workflow_id": "2b9d539d-aec4-436c-aa6d-27eef1c96627",
  "created_at": "2025-09-19T07:03:57.371916"
}