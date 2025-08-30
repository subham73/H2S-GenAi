## 🎯 Hackathon Objective

To develop an **AI-powered system** that automatically converts healthcare software requirements into **compliant, traceable test cases**, integrated with enterprise toolchains. The goal is to reduce manual QA effort, accelerate product cycles, and ensure regulatory alignment in a highly sensitive domain.

---

## 💡 MVP

| **Feature Area**                     | **Description**                                                                          |
| ------------------------------------ | ---------------------------------------------------------------------------------------- |
| **Multimodal Requirement Ingestion** | Accepts inputs from PDF, Word, XML, Markup, and ALM tools like Jira/Polarion             |
| **AI-Powered Test Generation**       | Uses Gemini/Vertex AI to parse requirements and generate test cases with compliance tags |
| **Compliance Mapping**               | Embeds FDA, IEC 62304, ISO 13485, GDPR rules into test logic and traceability            |
| **Traceability Matrix**              | Auto-generated bi-directional matrix linking requirements ↔ test cases ↔ defects         |
| **Enterprise Integration**           | Connects with Jira, Azure DevOps, Polarion via APIs for real-time sync                   |
| **GDPR-Compliant PoC Mode**          | Supports masked data and audit logs for privacy-safe pilot deployments                   |
| **Scalable Architecture**            | Microservices on Google Cloud with Firebase dashboards and BigQuery analytics            |

---

## 👥 Team Contributions


### Subir (Fullstack)

- Built upload interface and dashboard
- Developed traceability matrix UI
- Integrated frontend with Firebase and backend APIs
- Polished demo experience and export features 

### Hemant (Google Cloud) 

- Set up Vertex AI, BigQuery, Firebase
- Built ALM tool connectors (Jira, Azure DevOps)
- Enabled auto-sync and audit logging
- Deployed scalable microservices on GCP 

### Subham (AIML)

- Designed NLP pipeline using Gemini
- Built test case generation logic
- Mapped regulatory standards to AI outputs
- Led compliance tagging and traceability logic 

| **Intern** (Support) | QA, Documentation, Testing |

- Validated AI outputs and test cases
- Simulated GDPR PoC scenarios
- Assisted with integration testing and demo prep
- Maintained documentation and pitch materials |
