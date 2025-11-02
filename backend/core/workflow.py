import json
from typing import Dict
from backend.agents.compliance_checker import ComplianceCheckAgent
from backend.agents.orchestrator import OrchestratorAgent
from backend.agents.testcase_generator import TestCaseGeneratorAgent
from backend.core.data_models import QAState
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai import ChatVertexAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
import os
from google.cloud import pubsub_v1
import json
import logging

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------------------------
# Reusable Pub/Sub Publisher
# Initialize the client once and reuse it.
# ----------------------------------------------------------------------------------------------
try:
    publisher = pubsub_v1.PublisherClient()
except Exception as e:
    publisher = None
    logger.error(f"Could not initialize Pub/Sub publisher client: {e}")

def finalize_workflow(state: QAState) -> QAState:
    state.current_step = "complete"
    state.workflow_complete = True
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

def generate_traceability_matrix(state: QAState) -> Dict:
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
    export_data = {
        "workflow_id": state.workflow_id,
        "created_at": state.created_at.isoformat(),
        "regulatory_requirements": state.regulatory_requirements,
        "test_cases": [],
        "compliance_results": []
    }
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

def create_qa_workflow():
    llm = ChatVertexAI(
        model="gemini-2.5-flash", 
        temperature=0.2,
    )                              
    orchestrator = OrchestratorAgent(llm)
    test_generator = TestCaseGeneratorAgent(llm)
    compliance_checker = ComplianceCheckAgent(llm)
    workflow = StateGraph(QAState)
    workflow.add_node("orchestrator", orchestrator.run)
    workflow.add_node("test_generator", test_generator.run)
    # workflow.add_node("compliance_checker", compliance_checker.run)
    workflow.add_node("finalize", finalize_workflow)
    workflow.set_entry_point("orchestrator")
    workflow.add_edge("orchestrator", "test_generator")
    # workflow.add_edge("test_generator", "finalize") # changed to finalize , change it back
    # workflow.add_edge("compliance_checker", "finalize")
    workflow.add_edge("test_generator", END)
    return workflow.compile()

# ----------------------------------------------------------------------------------------------
# Agent Integration Logic to trigger message publishing
# ----------------------------------------------------------------------------------------------

def publish_message(project_id, topic_name, data):
    """
    Publishes a JSON-formatted message to a specified Pub/Sub topic.

    Args:
        project_id (str): Your Google Cloud project ID.
        topic_name (str): The name of the Pub/Sub topic.
        data (dict): A dictionary to be sent as the message payload.
    """
    if not publisher:
        logger.error("Publisher client is not available. Cannot publish message.")
        return

    topic_path = publisher.topic_path(project_id, topic_name)
    
    # Data must be a bytestring, so we encode the JSON data.
    message_bytes = json.dumps(data).encode("utf-8")
    
    try:
        # The publish() method returns a future.
        future = publisher.publish(topic_path, message_bytes)
        message_id = future.result()  # Wait for the publish to complete.
        logger.info(f"Successfully published message {message_id} to topic '{topic_name}'.")
    except Exception as e:
        logger.error(f"Failed to publish message to topic '{topic_name}': {e}")

def publish_requirements_notification(new_req_id: str):
    """
    Example of what the agent does after inserting a requirement into BigQuery.
    """
    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
    logger.info(f"Agent successfully inserted requirement {new_req_id} into BigQuery.")

    # Now, publish a notification to trigger the JIRA Requirement sync
    if GCP_PROJECT_ID:
        message_payload = {"req_id": new_req_id}
        publish_message(GCP_PROJECT_ID, "requirement-updates", message_payload)
    else:
        logger.error("GCP_PROJECT_ID not set. Cannot publish to Pub/Sub.")

def publish_issues_notificaiton(new_issue_id):
    """
    Example of what the agent does after inserting an issue into BigQuery.
    """
    # ...existing agent logic to insert the issue ...
    logger.info(f"Agent successfully inserted issue {new_issue_id} into BigQuery.")

    # Now, publish a notification to trigger the JIRA defect creation
    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
    if GCP_PROJECT_ID:
        message_payload = {"issue_id": new_issue_id}
        publish_message(GCP_PROJECT_ID, "test-failures", message_payload)
    else:
        logger.error("GCP_PROJECT_ID not set. Cannot publish to Pub/Sub.")            