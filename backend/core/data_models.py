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
    compliance_status: str
    recommendations: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    violations: List[str] = Field(default_factory=list, description="Detected compliance risks")
    regulatory_citations: List[str] = Field(default_factory=list, description="Relevant regulatory references")

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

# completeQA = {
#   "requirement": "The system shall provide patients and healthcare providers the ability to book, reschedule, and cancel appointments. Automated reminders must be sent via SMS/email to patients and staff prior to scheduled appointments. The schedule must reflect real-time availability and prevent double-booking of resources (doctors, rooms, equipment).",
#   "requirement_analysis": {
#     "functional_areas": {
#       "modules": [
#         "Appointment Management",
#         "Scheduling Engine",
#         "Notification System",
#         "Resource Management"
#       ],
#       "workflows": [
#         "Appointment Booking (Patient initiated)",
#         "Appointment Booking (Provider initiated)",
#         "Appointment Rescheduling (Patient initiated)",
#         "Appointment Rescheduling (Provider initiated)",
#         "Appointment Cancellation (Patient initiated)",
#         "Appointment Cancellation (Provider initiated)",
#         "Automated Reminder Generation and Delivery",
#         "Real-time Availability Update"
#       ],
#       "use_cases": [
#         "Book an Appointment as a Patient",
#         "Book an Appointment as a Healthcare Provider",
#         "Reschedule an Appointment as a Patient",
#         "Reschedule an Appointment as a Healthcare Provider",
#         "Cancel an Appointment as a Patient",
#         "Cancel an Appointment as a Healthcare Provider",
#         "Receive Appointment Reminder (Patient)",
#         "Receive Appointment Reminder (Staff)",
#         "View Real-time Resource Availability",
#         "System Prevents Double-Booking"
#       ]
#     },
#     "security_considerations": {
#       "data_protection": "All patient and provider data, including appointment details, must be encrypted at rest and in transit. Measures to prevent unauthorized access, modification, or disclosure of sensitive health information (PHI) are critical.",
#       "user_authentication": "Strong authentication mechanisms (e.g., multi-factor authentication) for both patients and healthcare providers to ensure only authorized users can access the system.",
#       "authorization": "Role-based access control (RBAC) to define and enforce permissions based on user roles (e.g., patient, doctor, administrator, scheduler). Patients can only manage their own appointments, while providers can manage their own and potentially others' schedules based on their role.",
#       "access_control": "Granular access controls to ensure that users can only view or modify data relevant to their role and specific permissions. For instance, a patient can only see their own appointments, while a doctor can see their own schedule and patient details for their appointments.",
#       "logging": "Comprehensive logging of all user activities (e.g., appointment booking, rescheduling, cancellation, data access) and system events (e.g., reminder delivery, system errors) for audit trails and incident investigation.",
#       "incident_detection": "Mechanisms to detect and alert on suspicious activities, unauthorized access attempts, data breaches, or system anomalies. This includes monitoring logs and system behavior for deviations from normal patterns."
#     },
#     "compliance_requirements": {
#       "regulations": [
#         "HIPAA",
#         "GDPR",
#         "PIPEDA (if applicable in Canada)",
#         "CCPA (if applicable in California)"
#       ],
#       "compliance_measures": {
#         "HIPAA": "Implement technical safeguards (encryption, access controls, audit logs), administrative safeguards (security policies, training), and physical safeguards to protect Protected Health Information (PHI) related to appointments and patient identities. Ensure business associate agreements (BAAs) are in place with any third-party services handling PHI (e.g., SMS/email providers).",
#         "GDPR": "Ensure explicit consent for data processing, provide data subjects with rights (access, rectification, erasure, portability), implement data minimization, privacy by design, and conduct Data Protection Impact Assessments (DPIAs). Securely process personal data, including contact information for reminders, and ensure data is stored within compliant jurisdictions or with appropriate transfer mechanisms."
#       },
#       "auditability": "The system must maintain immutable audit trails for all appointment-related actions (creation, modification, cancellation), user logins, and data access. These logs should include timestamps, user identities, and details of the action performed, enabling reconstruction of events for compliance audits and investigations."
#     },
#     "data_handling": {
#       "data_entities": [
#         "Patient Records (Name, Contact Info, Appointment History)",
#         "Healthcare Provider Records (Name, Specialization, Schedule, Contact Info)",
#         "Appointment Records (Date, Time, Duration, Service Type, Patient ID, Provider ID, Resource IDs, Status)",
#         "Resource Records (Room, Equipment, Availability)",
#         "Notification Logs (Recipient, Message Content, Delivery Status, Timestamp)"
#       ],
#       "data_collection": "Data will be collected through secure web forms or API integrations when patients or providers book, reschedule, or cancel appointments. Patient contact information for reminders will be collected during the booking process.",
#       "data_storage": "All data will be stored in secure, encrypted databases. Patient and provider data will be logically separated or pseudonymized where possible. Storage infrastructure must comply with relevant healthcare data regulations.",
#       "data_transmission": "All data transmitted between the client (patient/provider interface) and the server, and between system components, must be encrypted using industry-standard protocols (e.g., TLS 1.2+). SMS and email reminders should be sent via secure, compliant third-party services.",
#       "retention_policy": "Appointment and patient data will be retained for a period compliant with legal and regulatory requirements (e.g., HIPAA, state medical record retention laws), typically several years after the last patient interaction. Specific retention periods will be defined per data type.",
#       "backup_policy": "Regular, automated backups of all critical data (patient, provider, appointment, resource schedules) will be performed. Backups will be encrypted, stored off-site, and regularly tested for restorability to ensure business continuity and data integrity.",
#       "deletion_policy": "Data deletion will adhere to regulatory requirements and user requests (e.g., GDPR 'right to be forgotten'). Data marked for deletion will be securely purged from primary storage and backups after the defined retention period, ensuring irretrievability."
#     },
#     "other_critical_aspects": {
#       "interoperability": "Potential integration with existing Electronic Health Record (EHR) or Practice Management Systems (PMS) to synchronize patient demographics, provider schedules, and potentially appointment types. Adherence to standards like HL7 FHIR for data exchange.",
#       "integration": "Integration with SMS gateway providers for text message reminders, email service providers for email reminders, and potentially calendar systems (e.g., Google Calendar, Outlook Calendar) for provider schedule synchronization.",
#       "performance": "The system must provide real-time availability updates and process booking, rescheduling, and cancellation requests with minimal latency to ensure a smooth user experience and prevent double-booking. The notification system must reliably send reminders in a timely manner.",
#       "scalability": "The system architecture must be scalable to handle a growing number of patients, providers, appointments, and concurrent users without degradation in performance. This includes scaling database, application, and notification services.",
#       "usability": "Intuitive and user-friendly interfaces for both patients (for booking/managing appointments) and healthcare providers/staff (for managing schedules, resources, and patient appointments). Clear navigation, accessible design, and efficient workflows are essential.",
#       "monitoring": "Continuous monitoring of system health, performance metrics (e.g., response times, error rates), resource utilization, and security events. Alerts should be configured for critical issues, and dashboards should provide real-time insights into system operations and reminder delivery status."
#     }
#   },
#   "regulatory_requirements": [
#     "iso",
#     "fda"
#   ],
#   "current_step": "compliance_check",
#   "messages": [
#     {
#       "content": "Starting QA automation workflow",
#       "additional_kwargs": {},
#       "response_metadata": {},
#       "type": "human",
#       "name": null,
#       "id": null
#     },
#     {
#       "content": "Generating test cases",
#       "additional_kwargs": {},
#       "response_metadata": {},
#       "type": "human",
#       "name": null,
#       "id": null
#     },
#     {
#       "content": "Generated 43 test cases",
#       "additional_kwargs": {},
#       "response_metadata": {},
#       "type": "ai",
#       "name": null,
#       "id": null
#     }
#   ],
#   "test_cases": [
#     {
#       "id": "TC-FUNC-AM-001",
#       "title": "Patient Initiated Appointment Booking - Happy Path",
#       "description": "Verify a patient can successfully book a new appointment for an available slot with a specific provider and service.",
#       "preconditions": [
#         "Patient account exists and is logged in.",
#         "Provider has available slots for the selected service.",
#         "Required resources (e.g., room, equipment) are available."
#       ],
#       "steps": [
#         "Patient navigates to the 'Book Appointment' section.",
#         "Patient selects a service type.",
#         "Patient selects a preferred provider (if applicable).",
#         "Patient selects an available date and time slot from the calendar.",
#         "Patient confirms appointment details.",
#         "Patient submits the booking request."
#       ],
#       "expected_results": [
#         "Appointment is successfully booked and confirmed.",
#         "Patient receives an immediate on-screen confirmation.",
#         "Patient receives an email/SMS confirmation.",
#         "The selected time slot is marked as unavailable in the scheduling engine.",
#         "Provider's schedule reflects the new appointment."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-FUNC-AM-002",
#       "title": "Patient Initiated Appointment Booking - No Availability",
#       "description": "Verify the system correctly informs the patient when no slots are available for their selected criteria.",
#       "preconditions": [
#         "Patient account exists and is logged in.",
#         "No available slots for the selected service/provider/date range."
#       ],
#       "steps": [
#         "Patient navigates to the 'Book Appointment' section.",
#         "Patient selects a service type.",
#         "Patient selects a preferred provider (if applicable).",
#         "Patient attempts to select a date/time for which no slots are available."
#       ],
#       "expected_results": [
#         "System displays a message indicating no availability for the selected criteria.",
#         "System suggests alternative dates, times, or providers if possible."
#       ],
#       "priority": "Medium",
#       "regulatory_tags": [],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-FUNC-AM-003",
#       "title": "Provider Initiated Appointment Booking - Existing Patient",
#       "description": "Verify a healthcare provider or staff can book an appointment for an existing patient.",
#       "preconditions": [
#         "Provider/Staff account exists and is logged in.",
#         "Existing patient record is accessible.",
#         "Provider has available slots for the selected service."
#       ],
#       "steps": [
#         "Provider/Staff navigates to the scheduling interface.",
#         "Provider/Staff selects 'Book Appointment for Patient'.",
#         "Provider/Staff searches for and selects an existing patient.",
#         "Provider/Staff selects a service type, date, and available time slot.",
#         "Provider/Staff confirms appointment details.",
#         "Provider/Staff submits the booking request."
#       ],
#       "expected_results": [
#         "Appointment is successfully booked and confirmed.",
#         "Patient receives an email/SMS confirmation.",
#         "The selected time slot is marked as unavailable.",
#         "Provider's schedule reflects the new appointment."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-FUNC-AM-004",
#       "title": "Patient Initiated Appointment Rescheduling - Happy Path",
#       "description": "Verify a patient can successfully reschedule their existing appointment to a new available slot.",
#       "preconditions": [
#         "Patient account exists and is logged in.",
#         "Patient has an upcoming appointment.",
#         "There are available slots for rescheduling."
#       ],
#       "steps": [
#         "Patient navigates to 'My Appointments'.",
#         "Patient selects an upcoming appointment to reschedule.",
#         "Patient selects 'Reschedule' option.",
#         "Patient selects a new available date and time slot.",
#         "Patient confirms the rescheduling.",
#         "Patient submits the rescheduling request."
#       ],
#       "expected_results": [
#         "Appointment is successfully rescheduled.",
#         "Patient receives an on-screen confirmation.",
#         "Patient receives an email/SMS confirmation of the rescheduled appointment.",
#         "The original time slot is released and becomes available.",
#         "The new time slot is marked as unavailable.",
#         "Provider's schedule reflects the updated appointment time."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-FUNC-AM-005",
#       "title": "Provider Initiated Appointment Rescheduling - Happy Path",
#       "description": "Verify a provider or staff can successfully reschedule a patient's appointment.",
#       "preconditions": [
#         "Provider/Staff account exists and is logged in.",
#         "Patient has an upcoming appointment with the provider.",
#         "There are available slots for rescheduling."
#       ],
#       "steps": [
#         "Provider/Staff navigates to their schedule or patient's appointment list.",
#         "Provider/Staff selects a patient's upcoming appointment to reschedule.",
#         "Provider/Staff selects 'Reschedule' option.",
#         "Provider/Staff selects a new available date and time slot.",
#         "Provider/Staff confirms the rescheduling.",
#         "Provider/Staff submits the rescheduling request."
#       ],
#       "expected_results": [
#         "Appointment is successfully rescheduled.",
#         "Patient receives an email/SMS confirmation of the rescheduled appointment.",
#         "The original time slot is released and becomes available.",
#         "The new time slot is marked as unavailable.",
#         "Provider's schedule reflects the updated appointment time."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-FUNC-AM-006",
#       "title": "Patient Initiated Appointment Cancellation - Happy Path",
#       "description": "Verify a patient can successfully cancel their upcoming appointment within the allowed cancellation period.",
#       "preconditions": [
#         "Patient account exists and is logged in.",
#         "Patient has an upcoming appointment.",
#         "The cancellation deadline for the appointment has not passed."
#       ],
#       "steps": [
#         "Patient navigates to 'My Appointments'.",
#         "Patient selects an upcoming appointment to cancel.",
#         "Patient selects 'Cancel Appointment' option.",
#         "Patient confirms the cancellation.",
#         "Patient submits the cancellation request."
#       ],
#       "expected_results": [
#         "Appointment is successfully cancelled.",
#         "Patient receives an on-screen confirmation.",
#         "Patient receives an email/SMS confirmation of the cancellation.",
#         "The cancelled time slot is released and becomes available.",
#         "Provider's schedule reflects the cancelled appointment."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-FUNC-AM-007",
#       "title": "Patient Initiated Appointment Cancellation - After Deadline",
#       "description": "Verify a patient cannot cancel an appointment after the defined cancellation deadline and receives appropriate notification.",
#       "preconditions": [
#         "Patient account exists and is logged in.",
#         "Patient has an upcoming appointment.",
#         "The cancellation deadline for the appointment has passed."
#       ],
#       "steps": [
#         "Patient navigates to 'My Appointments'.",
#         "Patient selects an upcoming appointment.",
#         "Patient attempts to select 'Cancel Appointment' option."
#       ],
#       "expected_results": [
#         "The 'Cancel Appointment' option is disabled or not visible.",
#         "If attempted, system displays a message indicating the cancellation deadline has passed and cancellation is not allowed."
#       ],
#       "priority": "Medium",
#       "regulatory_tags": [],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-FUNC-AM-008",
#       "title": "Provider Initiated Appointment Cancellation - Happy Path",
#       "description": "Verify a provider or staff can successfully cancel a patient's appointment.",
#       "preconditions": [
#         "Provider/Staff account exists and is logged in.",
#         "Patient has an upcoming appointment with the provider."
#       ],
#       "steps": [
#         "Provider/Staff navigates to their schedule or patient's appointment list.",
#         "Provider/Staff selects a patient's upcoming appointment to cancel.",
#         "Provider/Staff selects 'Cancel Appointment' option.",
#         "Provider/Staff confirms the cancellation.",
#         "Provider/Staff submits the cancellation request."
#       ],
#       "expected_results": [
#         "Appointment is successfully cancelled.",
#         "Patient receives an email/SMS notification of the cancellation.",
#         "The cancelled time slot is released and becomes available.",
#         "Provider's schedule reflects the cancelled appointment."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-FUNC-NS-001",
#       "title": "Automated Reminder Generation and Delivery - Email",
#       "description": "Verify the system generates and delivers appointment reminders via email to patients at configured intervals.",
#       "preconditions": [
#         "Patient has a confirmed upcoming appointment.",
#         "Patient has a valid email address on file.",
#         "Reminder schedule is configured (e.g., 24 hours before appointment)."
#       ],
#       "steps": [
#         "Wait for the configured reminder time (e.g., 24 hours before appointment).",
#         "Check the patient's registered email inbox."
#       ],
#       "expected_results": [
#         "Patient receives an email reminder containing correct appointment details (date, time, provider, service).",
#         "The email sender is identifiable as the healthcare system/provider.",
#         "Notification log records the successful delivery of the email reminder."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-FUNC-NS-002",
#       "title": "Automated Reminder Generation and Delivery - SMS",
#       "description": "Verify the system generates and delivers appointment reminders via SMS to patients at configured intervals.",
#       "preconditions": [
#         "Patient has a confirmed upcoming appointment.",
#         "Patient has a valid mobile number on file.",
#         "Reminder schedule is configured (e.g., 2 hours before appointment)."
#       ],
#       "steps": [
#         "Wait for the configured reminder time (e.g., 2 hours before appointment).",
#         "Check the patient's registered mobile device for SMS."
#       ],
#       "expected_results": [
#         "Patient receives an SMS reminder containing correct appointment details (date, time, provider, service).",
#         "The SMS sender is identifiable.",
#         "Notification log records the successful delivery of the SMS reminder."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-FUNC-NS-003",
#       "title": "Staff Reminder Notification",
#       "description": "Verify staff members receive appropriate notifications for upcoming appointments or schedule changes.",
#       "preconditions": [
#         "Staff account exists and is logged in.",
#         "Staff has upcoming appointments assigned.",
#         "Staff notification preferences are configured."
#       ],
#       "steps": [
#         "Book an appointment for a patient with the staff member.",
#         "Wait for the configured notification time (e.g., start of day summary, 15 mins before appointment).",
#         "Check staff's notification dashboard or email/SMS."
#       ],
#       "expected_results": [
#         "Staff receives a notification with relevant appointment details.",
#         "Notification log records the successful delivery of the staff notification."
#       ],
#       "priority": "Medium",
#       "regulatory_tags": [],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-FUNC-SE-001",
#       "title": "Real-time Availability Update",
#       "description": "Verify that the scheduling engine updates provider and resource availability in real-time after an appointment action.",
#       "preconditions": [
#         "Provider has available slots.",
#         "Patient account exists and is logged in."
#       ],
#       "steps": [
#         "Open two browser sessions: one for a patient viewing availability, one for a provider/staff.",
#         "In patient session, view a specific provider's availability for a date.",
#         "In provider/staff session, book an appointment for that provider and date/time.",
#         "Refresh the patient's availability view."
#       ],
#       "expected_results": [
#         "The booked time slot is immediately marked as unavailable in the patient's view.",
#         "If the booked slot is cancelled, it should become available again in real-time."
#       ],
#       "priority": "High",
#       "regulatory_tags": [],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-FUNC-SE-002",
#       "title": "System Prevents Double-Booking",
#       "description": "Verify the scheduling engine prevents double-booking of a provider or a critical resource for the same time slot.",
#       "preconditions": [
#         "Provider has an available slot.",
#         "Two separate users (e.g., two patients or a patient and a staff) attempt to book the same slot concurrently."
#       ],
#       "steps": [
#         "User A initiates booking for Provider X at Time Y.",
#         "Before User A completes booking, User B initiates booking for Provider X at Time Y.",
#         "User A completes booking.",
#         "User B attempts to complete booking."
#       ],
#       "expected_results": [
#         "Only one booking request is successful.",
#         "The second booking attempt is rejected with a message indicating the slot is no longer available.",
#         "The system maintains data integrity for provider and resource schedules."
#       ],
#       "priority": "High",
#       "regulatory_tags": [],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-FUNC-RM-001",
#       "title": "View Real-time Resource Availability",
#       "description": "Verify that staff can view the real-time availability of resources (rooms, equipment) to aid in scheduling.",
#       "preconditions": [
#         "Staff account exists and is logged in.",
#         "Multiple resources are configured in the system."
#       ],
#       "steps": [
#         "Staff navigates to the 'Resource Management' or 'Scheduling' section.",
#         "Staff selects a specific date and time range.",
#         "Staff views the availability of various resources."
#       ],
#       "expected_results": [
#         "The system displays a clear overview of resource availability (e.g., 'Room A - Available', 'Equipment B - In Use').",
#         "Availability updates dynamically as resources are booked or released."
#       ],
#       "priority": "Medium",
#       "regulatory_tags": [],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-SEC-DP-001",
#       "title": "Data Encryption at Rest - PHI",
#       "description": "Verify that sensitive patient health information (PHI) stored in the database is encrypted at rest.",
#       "preconditions": [
#         "Patient data (including appointment details, contact info) is stored in the system."
#       ],
#       "steps": [
#         "Attempt to access the underlying database storage directly (simulated, or verify configuration/documentation for blackbox).",
#         "Inspect stored data for PHI."
#       ],
#       "expected_results": [
#         "PHI data is stored in an encrypted format, rendering it unreadable without decryption keys.",
#         "No plain-text PHI is discoverable in storage."
#       ],
#       "priority": "Critical",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR",
#         "PHI"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-SEC-DP-002",
#       "title": "Data Encryption in Transit - Client to Server",
#       "description": "Verify all data transmitted between client applications (patient/provider interfaces) and the server is encrypted using TLS 1.2+.",
#       "preconditions": [
#         "Access to a network traffic monitoring tool (e.g., Wireshark, browser developer tools)."
#       ],
#       "steps": [
#         "Access the application (patient portal, provider dashboard) via a web browser.",
#         "Perform actions involving data transmission (e.g., login, book appointment, view schedule).",
#         "Monitor network traffic using browser developer tools or a proxy."
#       ],
#       "expected_results": [
#         "All HTTP requests are redirected to HTTPS.",
#         "Network traffic shows encrypted payloads (TLS 1.2 or higher).",
#         "No sensitive data (PHI, credentials) is transmitted in plain text."
#       ],
#       "priority": "Critical",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR",
#         "PHI"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-SEC-AUTH-001",
#       "title": "Strong User Authentication - MFA Enforcement",
#       "description": "Verify Multi-Factor Authentication (MFA) is enforced for both patient and healthcare provider logins.",
#       "preconditions": [
#         "User accounts (patient and provider) are configured for MFA."
#       ],
#       "steps": [
#         "Attempt to log in as a patient with valid credentials.",
#         "Attempt to log in as a healthcare provider with valid credentials."
#       ],
#       "expected_results": [
#         "After entering primary credentials, the system prompts for a second factor (e.g., OTP from authenticator app, SMS code, email code).",
#         "Login is successful only after providing both factors correctly.",
#         "Incorrect second factor input prevents login."
#       ],
#       "priority": "Critical",
#       "regulatory_tags": [
#         "HIPAA",
#         "MFA"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-SEC-AUTH-002",
#       "title": "Session Management - Inactivity Timeout",
#       "description": "Verify user sessions automatically terminate after a period of inactivity to prevent unauthorized access.",
#       "preconditions": [
#         "Patient or Provider is logged into the system.",
#         "Inactivity timeout period is configured (e.g., 15 minutes)."
#       ],
#       "steps": [
#         "Log in as a user (patient or provider).",
#         "Leave the session idle for longer than the configured inactivity timeout.",
#         "Attempt to perform an action (e.g., navigate to another page, click a button)."
#       ],
#       "expected_results": [
#         "The user is automatically logged out.",
#         "The user is redirected to the login page or an 'session expired' message is displayed.",
#         "No actions can be performed without re-authentication."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "HIPAA"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-SEC-RBAC-001",
#       "title": "Role-Based Access Control - Patient Permissions",
#       "description": "Verify a patient user can only access and manage their own appointments and personal data.",
#       "preconditions": [
#         "Patient A is logged in.",
#         "Patient B has existing appointments."
#       ],
#       "steps": [
#         "Patient A navigates to 'My Appointments'.",
#         "Patient A attempts to search for or view appointments belonging to Patient B.",
#         "Patient A attempts to modify or cancel an appointment belonging to Patient B."
#       ],
#       "expected_results": [
#         "Patient A can only view and manage their own appointments.",
#         "Attempts to access or modify other patients' data are denied or result in an 'access denied' error.",
#         "No information about Patient B's appointments or PHI is disclosed to Patient A."
#       ],
#       "priority": "Critical",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR",
#         "RBAC",
#         "PHI"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-SEC-RBAC-002",
#       "title": "Role-Based Access Control - Provider Permissions",
#       "description": "Verify a healthcare provider can manage their own schedule and access patient details only for their scheduled appointments.",
#       "preconditions": [
#         "Provider A is logged in.",
#         "Provider B has appointments with patients.",
#         "Patient X has an appointment with Provider A.",
#         "Patient Y has an appointment with Provider B."
#       ],
#       "steps": [
#         "Provider A navigates to their schedule.",
#         "Provider A attempts to view Provider B's full schedule.",
#         "Provider A attempts to access PHI for Patient Y (who is not scheduled with Provider A).",
#         "Provider A views PHI for Patient X (who is scheduled with Provider A)."
#       ],
#       "expected_results": [
#         "Provider A can view and manage their own schedule.",
#         "Provider A is denied access to Provider B's full schedule (unless explicitly granted by higher role).",
#         "Provider A is denied access to PHI of Patient Y.",
#         "Provider A can successfully access PHI of Patient X for their scheduled appointment."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR",
#         "RBAC",
#         "PHI"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-SEC-LOG-001",
#       "title": "Comprehensive Logging - Appointment Actions",
#       "description": "Verify all appointment-related actions (booking, rescheduling, cancellation) are logged with sufficient detail for audit trails.",
#       "preconditions": [
#         "Access to system audit logs."
#       ],
#       "steps": [
#         "Log in as a patient and book an appointment.",
#         "Log in as the same patient and reschedule the appointment.",
#         "Log in as the same patient and cancel the appointment.",
#         "Access the system's audit logs."
#       ],
#       "expected_results": [
#         "Audit logs contain entries for 'Appointment Booked', 'Appointment Rescheduled', and 'Appointment Cancelled'.",
#         "Each log entry includes: timestamp, user ID, action performed, patient ID, provider ID, original/new appointment details.",
#         "Logs are immutable and cannot be tampered with by regular users."
#       ],
#       "priority": "Critical",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR",
#         "Auditability"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-SEC-LOG-002",
#       "title": "Comprehensive Logging - User Login and Data Access",
#       "description": "Verify all user login attempts (success/failure) and access to sensitive data are logged.",
#       "preconditions": [
#         "Access to system audit logs."
#       ],
#       "steps": [
#         "Attempt a successful login as a patient.",
#         "Attempt a failed login as a patient (incorrect password).",
#         "Log in as a provider and view a patient's PHI.",
#         "Access the system's audit logs."
#       ],
#       "expected_results": [
#         "Audit logs contain entries for 'Successful Login' and 'Failed Login Attempt' with user ID, IP address, and timestamp.",
#         "Audit logs contain entries for 'PHI Accessed' with user ID, patient ID, and timestamp.",
#         "Logs are immutable and cannot be tampered with."
#       ],
#       "priority": "Critical",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR",
#         "Auditability",
#         "PHI"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-SEC-ID-001",
#       "title": "Incident Detection - Failed Login Attempts Alert",
#       "description": "Verify the system detects and alerts administrators about suspicious patterns of failed login attempts.",
#       "preconditions": [
#         "Administrator account exists.",
#         "Alerting mechanism for security incidents is configured."
#       ],
#       "steps": [
#         "Attempt multiple (e.g., 5-10) failed login attempts for a single user account within a short period.",
#         "Check administrator's alert dashboard or email/SMS notifications."
#       ],
#       "expected_results": [
#         "An alert is triggered and sent to administrators regarding suspicious login activity.",
#         "The system may temporarily lock the user account after a threshold of failed attempts.",
#         "The incident is logged in the security event logs."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "HIPAA"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-COMP-HIPAA-001",
#       "title": "HIPAA Compliance - Technical Safeguards (Access Control)",
#       "description": "Verify that technical safeguards for access control, as required by HIPAA, are implemented and effective.",
#       "preconditions": [
#         "Multiple user roles (patient, provider, admin) are defined.",
#         "PHI data exists in the system."
#       ],
#       "steps": [
#         "Attempt to access PHI as an unauthorized user (e.g., patient trying to view another patient's data).",
#         "Attempt to modify PHI as an unauthorized user.",
#         "Verify role-based access controls are enforced (refer to TC-SEC-RBAC-001, TC-SEC-RBAC-002)."
#       ],
#       "expected_results": [
#         "Unauthorized access to PHI is consistently denied.",
#         "Access is restricted based on user roles and permissions.",
#         "All access attempts (authorized and unauthorized) are logged for audit."
#       ],
#       "priority": "Critical",
#       "regulatory_tags": [
#         "HIPAA",
#         "PHI",
#         "RBAC"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-COMP-HIPAA-002",
#       "title": "HIPAA Compliance - Business Associate Agreement (BAA) Support",
#       "description": "Verify the system's design and third-party integrations support HIPAA BAA requirements for handling PHI.",
#       "preconditions": [
#         "System integrates with third-party services (e.g., SMS gateway, email provider)."
#       ],
#       "steps": [
#         "Review documentation for third-party service providers.",
#         "Verify that the system's configuration allows for the use of BAA-compliant services.",
#         "Confirm that PHI is not transmitted to non-BAA compliant entities."
#       ],
#       "expected_results": [
#         "All third-party services handling PHI are identified as BAA-compliant.",
#         "System configuration prevents sending PHI to non-compliant services.",
#         "Documentation confirms BAA agreements are in place or system design facilitates their use."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "HIPAA",
#         "PHI",
#         "BAA"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-COMP-GDPR-001",
#       "title": "GDPR Compliance - Data Subject Consent",
#       "description": "Verify explicit consent is obtained from data subjects (patients) for the processing of their personal data, especially for reminders.",
#       "preconditions": [
#         "New patient registration or appointment booking process."
#       ],
#       "steps": [
#         "As a new patient, attempt to register or book an appointment.",
#         "Observe the data collection forms for contact information and other personal data.",
#         "Check for consent checkboxes or statements related to data processing and communication preferences."
#       ],
#       "expected_results": [
#         "Clear, unambiguous consent checkboxes are present for data processing (e.g., 'I agree to the processing of my data for appointment management').",
#         "Separate consent is obtained for marketing communications vs. essential service communications (reminders).",
#         "The system does not proceed with data processing without explicit consent where required."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "GDPR",
#         "Consent"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-COMP-GDPR-002",
#       "title": "GDPR Compliance - Right to Access and Rectification",
#       "description": "Verify patients can access their personal data and request rectification of inaccurate data.",
#       "preconditions": [
#         "Patient account exists and is logged in.",
#         "Patient has personal data (contact info, appointment history) stored."
#       ],
#       "steps": [
#         "Patient navigates to their profile/account settings.",
#         "Patient views their stored personal data.",
#         "Patient attempts to update their contact information (e.g., phone number, email address).",
#         "Patient submits a request to rectify other data if direct editing is not available."
#       ],
#       "expected_results": [
#         "Patient can view all personal data stored about them.",
#         "Patient can successfully update editable personal data.",
#         "If data is not directly editable, a clear process for requesting rectification is provided (e.g., contact support form).",
#         "Changes are reflected accurately in the system."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "GDPR",
#         "Data Subject Rights"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-COMP-GDPR-003",
#       "title": "GDPR Compliance - Right to Erasure ('Right to be forgotten')",
#       "description": "Verify the system supports the patient's right to request deletion of their personal data.",
#       "preconditions": [
#         "Patient account exists and is logged in.",
#         "Patient has personal data and appointment history."
#       ],
#       "steps": [
#         "Patient navigates to their account settings or a dedicated privacy section.",
#         "Patient initiates a request for data deletion (e.g., 'Delete My Account' or 'Request Data Erasure').",
#         "Follow the system's process for data deletion (e.g., confirmation, waiting period)."
#       ],
#       "expected_results": [
#         "The system provides a clear mechanism for patients to request data erasure.",
#         "Upon successful request and verification, the patient's personal data is securely and irretrievably deleted from primary storage.",
#         "Confirmation is provided to the patient regarding the deletion.",
#         "Audit logs record the data deletion request and execution."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "GDPR",
#         "Data Subject Rights",
#         "Deletion Policy"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-COMP-AUDIT-001",
#       "title": "Auditability - Immutable Audit Trails",
#       "description": "Verify that audit trails for all critical actions are immutable and cannot be altered or deleted by unauthorized users.",
#       "preconditions": [
#         "Access to system audit logs (as an administrator or auditor).",
#         "Various user actions (login, booking, data access) have been performed."
#       ],
#       "steps": [
#         "Access the audit log interface.",
#         "Attempt to modify an existing log entry.",
#         "Attempt to delete an existing log entry.",
#         "Verify log integrity (e.g., checksums, chronological order)."
#       ],
#       "expected_results": [
#         "Attempts to modify or delete audit log entries are denied.",
#         "The system maintains the integrity and chronological order of all audit records.",
#         "Log entries include timestamps, user identities, and details of the action performed, enabling full event reconstruction."
#       ],
#       "priority": "Critical",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR",
#         "Auditability"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-DATA-COL-001",
#       "title": "Secure Data Collection - Web Forms",
#       "description": "Verify that patient and provider data collected via web forms is secure and protected against common vulnerabilities.",
#       "preconditions": [
#         "Access to patient registration and appointment booking forms."
#       ],
#       "steps": [
#         "Attempt to submit forms with malicious input (e.g., SQL injection strings, XSS scripts) in text fields.",
#         "Attempt to bypass client-side validation using browser developer tools.",
#         "Verify input validation on the server-side."
#       ],
#       "expected_results": [
#         "The system rejects malicious input and prevents successful injection attacks.",
#         "Server-side validation correctly handles invalid or malformed data, preventing data corruption or security breaches.",
#         "Only expected data types and formats are accepted."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-DATA-STORAGE-001",
#       "title": "Data Storage - Logical Separation/Pseudonymization",
#       "description": "Verify that patient and provider data is logically separated or pseudonymized where possible to enhance privacy.",
#       "preconditions": [
#         "Access to system data architecture documentation (for blackbox, infer from UI/API behavior).",
#         "Patient and provider data exists."
#       ],
#       "steps": [
#         "Observe how patient identifiers are linked to PHI in different parts of the system (e.g., scheduling view vs. detailed patient record).",
#         "If possible, query data via API to see if direct identifiers are used where not strictly necessary."
#       ],
#       "expected_results": [
#         "Direct patient identifiers (e.g., name, contact) are not displayed or used in contexts where only an anonymized or pseudonymized ID is sufficient (e.g., internal scheduling engine operations).",
#         "PHI is not easily linkable to individuals without appropriate authorization and decryption/de-pseudonymization processes.",
#         "Documentation confirms logical separation or pseudonymization strategies."
#       ],
#       "priority": "Medium",
#       "regulatory_tags": [
#         "GDPR",
#         "PHI",
#         "Privacy by Design"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-DATA-TRANS-001",
#       "title": "Data Transmission - Secure Third-Party Services for Reminders",
#       "description": "Verify that SMS and email reminders are sent via secure, compliant third-party services.",
#       "preconditions": [
#         "Patient has an upcoming appointment and valid contact info.",
#         "System is configured to send SMS/email reminders."
#       ],
#       "steps": [
#         "Trigger an appointment reminder (SMS and email).",
#         "Inspect the received SMS/email for sender information, headers, and any security indicators.",
#         "Review system documentation for chosen third-party providers."
#       ],
#       "expected_results": [
#         "Reminders are sent from a reputable and identifiable source.",
#         "Email headers indicate secure transmission (e.g., SPF, DKIM, DMARC validation).",
#         "Documentation confirms the use of HIPAA/GDPR compliant third-party services with appropriate BAAs (if applicable for HIPAA)."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR",
#         "BAA"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-DATA-RETENTION-001",
#       "title": "Data Retention Policy Adherence",
#       "description": "Verify that appointment and patient data is retained according to defined legal and regulatory requirements.",
#       "preconditions": [
#         "System has historical patient and appointment data.",
#         "Retention policies are documented (e.g., 7 years after last interaction)."
#       ],
#       "steps": [
#         "Identify a patient record and associated appointments that are past their retention period.",
#         "Attempt to access this data via the application or API (as an authorized user).",
#         "Verify that data older than the retention period is either archived, anonymized, or securely deleted."
#       ],
#       "expected_results": [
#         "Data past its retention period is not readily accessible in active system views.",
#         "System processes for archiving, anonymization, or deletion are in place and functioning as per policy.",
#         "Documentation clearly outlines retention periods for different data types."
#       ],
#       "priority": "Medium",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-DATA-BACKUP-001",
#       "title": "Backup Policy - Data Restorability",
#       "description": "Verify that critical data backups are restorable and maintain data integrity.",
#       "preconditions": [
#         "Regular, automated backups are configured and performed.",
#         "A test environment is available for restoration testing."
#       ],
#       "steps": [
#         "Simulate a data loss scenario in a test environment.",
#         "Initiate a data restoration process from a recent backup.",
#         "Verify the integrity and completeness of the restored data (patient, provider, appointment records)."
#       ],
#       "expected_results": [
#         "Data is successfully restored from backup.",
#         "All critical data (patient, provider, appointment, resource schedules) is present and accurate after restoration.",
#         "The restoration process is efficient and documented."
#       ],
#       "priority": "Critical",
#       "regulatory_tags": [
#         "HIPAA",
#         "GDPR"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-DATA-DELETION-001",
#       "title": "Deletion Policy - Secure Purging",
#       "description": "Verify that data marked for deletion is securely purged from primary storage and backups, ensuring irretrievability.",
#       "preconditions": [
#         "A patient has requested data erasure (GDPR 'right to be forgotten').",
#         "The system has processed the deletion request."
#       ],
#       "steps": [
#         "After a patient's data has been 'deleted' from the system (as per TC-COMP-GDPR-003).",
#         "Attempt to retrieve any remnants of that patient's data from primary storage (e.g., via API, database queries if possible).",
#         "Verify that the data is also purged from backups after the defined retention period for backups."
#       ],
#       "expected_results": [
#         "The deleted patient's data is no longer accessible or retrievable from the live system.",
#         "The data is securely purged from backups after the backup retention period, rendering it irretrievable.",
#         "No residual personal data is found in logs or other system components beyond their defined retention/purging schedules."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "GDPR",
#         "Deletion Policy"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-OTHER-INTOP-001",
#       "title": "Interoperability - EHR/PMS Patient Demographics Sync",
#       "description": "Verify that patient demographics can be synchronized between the scheduling system and an integrated EHR/PMS.",
#       "preconditions": [
#         "Integration with a test EHR/PMS system is configured.",
#         "A patient record exists in both systems."
#       ],
#       "steps": [
#         "Update a patient's contact information in the EHR/PMS.",
#         "Trigger a synchronization event (manual or wait for automated sync).",
#         "Verify the updated information is reflected in the scheduling system.",
#         "Perform the reverse: update in scheduling system and verify in EHR/PMS."
#       ],
#       "expected_results": [
#         "Patient demographic data (e.g., name, address, phone) is accurately synchronized between the systems.",
#         "Data conflicts are handled gracefully (e.g., latest update wins, or manual resolution).",
#         "Synchronization occurs within acceptable latency."
#       ],
#       "priority": "High",
#       "regulatory_tags": [
#         "HIPAA",
#         "HL7 FHIR"
#       ],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-OTHER-INTEG-001",
#       "title": "Integration - External Calendar Synchronization (Provider)",
#       "description": "Verify that a provider's schedule from the system can be synchronized with an external calendar (e.g., Google Calendar, Outlook).",
#       "preconditions": [
#         "Provider account exists.",
#         "Provider has configured integration with an external calendar.",
#         "Provider has appointments scheduled in the system."
#       ],
#       "steps": [
#         "Provider books a new appointment in the scheduling system.",
#         "Provider reschedules an existing appointment.",
#         "Provider cancels an existing appointment.",
#         "Check the provider's integrated external calendar."
#       ],
#       "expected_results": [
#         "New appointments appear in the external calendar.",
#         "Rescheduled appointments are updated in the external calendar.",
#         "Cancelled appointments are removed or marked as cancelled in the external calendar.",
#         "Synchronization occurs reliably and within a reasonable timeframe."
#       ],
#       "priority": "Medium",
#       "regulatory_tags": [],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-OTHER-PERF-001",
#       "title": "Performance - Real-time Availability Latency",
#       "description": "Verify that the system displays real-time availability updates with minimal latency under normal load.",
#       "preconditions": [
#         "Multiple providers and resources configured.",
#         "Concurrent users are viewing availability."
#       ],
#       "steps": [
#         "Simultaneously open multiple browser sessions viewing provider availability.",
#         "In one session, book an appointment for a specific slot.",
#         "Measure the time taken for the availability to update in other sessions."
#       ],
#       "expected_results": [
#         "Availability updates are reflected across all sessions within a few seconds (e.g., < 3 seconds).",
#         "The system remains responsive during availability checks and updates."
#       ],
#       "priority": "High",
#       "regulatory_tags": [],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-OTHER-PERF-002",
#       "title": "Performance - Notification Delivery Timeliness",
#       "description": "Verify that automated reminders are delivered within their configured timeframes.",
#       "preconditions": [
#         "Patient has an upcoming appointment.",
#         "Reminders are configured for specific delivery times (e.g., 24 hours, 2 hours before).",
#         "Access to notification logs."
#       ],
#       "steps": [
#         "Book an appointment and set reminder times.",
#         "Monitor the actual delivery time of email/SMS reminders.",
#         "Compare actual delivery time with configured delivery time and system timestamps in logs."
#       ],
#       "expected_results": [
#         "Reminders are delivered within a small margin of error from their scheduled time (e.g., +/- 5 minutes).",
#         "Notification logs accurately record delivery timestamps.",
#         "No significant delays are observed even during peak hours."
#       ],
#       "priority": "High",
#       "regulatory_tags": [],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-OTHER-USAB-001",
#       "title": "Usability - Patient Appointment Booking Workflow",
#       "description": "Verify the patient appointment booking workflow is intuitive and user-friendly.",
#       "preconditions": [
#         "Patient account exists and is logged in."
#       ],
#       "steps": [
#         "Navigate to the 'Book Appointment' section.",
#         "Attempt to book an appointment without prior knowledge of the system.",
#         "Observe the clarity of instructions, navigation, and feedback messages."
#       ],
#       "expected_results": [
#         "The booking process is easy to understand and complete in a minimal number of steps.",
#         "Clear visual cues and labels guide the user.",
#         "Error messages are helpful and actionable.",
#         "The interface is responsive and loads quickly."
#       ],
#       "priority": "Medium",
#       "regulatory_tags": [],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-OTHER-USAB-002",
#       "title": "Usability - Provider Schedule Management",
#       "description": "Verify the provider interface for managing schedules and appointments is efficient and user-friendly.",
#       "preconditions": [
#         "Provider account exists and is logged in.",
#         "Provider has existing appointments."
#       ],
#       "steps": [
#         "Navigate to the provider's schedule view.",
#         "Attempt to quickly identify available slots, booked appointments, and patient details.",
#         "Attempt to reschedule or cancel an appointment.",
#         "Observe the efficiency of these workflows."
#       ],
#       "expected_results": [
#         "The schedule view is clear, concise, and easy to read.",
#         "Actions like rescheduling and cancellation can be performed with minimal clicks.",
#         "Relevant patient information is easily accessible from the schedule view.",
#         "The interface supports efficient daily operations for providers."
#       ],
#       "priority": "Medium",
#       "regulatory_tags": [],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-OTHER-MON-001",
#       "title": "Monitoring - System Health Dashboard",
#       "description": "Verify that the system provides a comprehensive dashboard for monitoring overall system health and performance.",
#       "preconditions": [
#         "Administrator account exists and is logged in.",
#         "System is operational and processing requests."
#       ],
#       "steps": [
#         "Administrator navigates to the system monitoring dashboard.",
#         "Observe displayed metrics and statuses."
#       ],
#       "expected_results": [
#         "The dashboard displays real-time metrics such as CPU usage, memory usage, database connection status, and application response times.",
#         "Critical services (e.g., scheduling engine, notification service) show 'healthy' status.",
#         "Any anomalies or errors are highlighted."
#       ],
#       "priority": "High",
#       "regulatory_tags": [],
#       "traceability_id": ""
#     },
#     {
#       "id": "TC-OTHER-MON-002",
#       "title": "Monitoring - Alerting for Critical Issues",
#       "description": "Verify that critical system issues (e.g., service outages, high error rates) trigger immediate alerts to administrators.",
#       "preconditions": [
#         "Administrator account exists.",
#         "Alerting mechanisms are configured (e.g., email, SMS, PagerDuty integration)."
#       ],
#       "steps": [
#         "Simulate a critical system issue (e.g., temporarily disable a database connection in a test environment, or trigger a high volume of errors).",
#         "Check administrator's configured alert channels."
#       ],
#       "expected_results": [
#         "Administrators receive immediate alerts (e.g., email, SMS) detailing the critical issue.",
#         "The alert contains sufficient information to identify and begin troubleshooting the problem.",
#         "The issue is logged in the system's incident management system."
#       ],
#       "priority": "Critical",
#       "regulatory_tags": [],
#       "traceability_id": ""
#     }
#   ],
#   "compliance_results": [],
#   "errors": [],
#   "workflow_complete": false,
#   "workflow_id": "2b9d539d-aec4-436c-aa6d-27eef1c96627",
#   "created_at": "2025-09-19T07:03:57.371916"
# }