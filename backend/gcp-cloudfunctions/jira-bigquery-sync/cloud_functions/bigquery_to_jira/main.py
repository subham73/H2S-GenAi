import functions_framework
import json
import logging
from google.cloud import bigquery
import requests
from datetime import datetime
import os
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.getenv('GCP_PROJECT_ID')
DATASET_ID = os.getenv('BIGQUERY_DATASET_ID', 'healthcare_data')
JIRA_BASE_URL = os.getenv('JIRA_BASE_URL')
JIRA_USERNAME = os.getenv('JIRA_USERNAME')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY')

# Lazily initialized clients to improve cold start times and prevent startup errors.
_bigquery_client = None

def get_bigquery_client():
    """Lazily initialize and return a BigQuery client."""
    global _bigquery_client
    if not _bigquery_client:
        _bigquery_client = bigquery.Client()
    return _bigquery_client


#This decorator is the bridge that connects a Pub/Sub topic to the following Python function, allowing it to react to events happening 
#in the cloud environment automatically.
@functions_framework.cloud_event                # Register the function as an event-driven Cloud Function.
def create_alm_defect(cloud_event):
    """
    Create ALM(JIRA/Azure/Polarian) defect from test failure events
    Triggered by Pub/Sub messages from test execution failures
    """
    try:
        # Decode and parse Pub/Sub message
        if 'data' not in cloud_event.data.get('message', {}):
            logger.warning("Pub/Sub message missing 'data' field.")
            return

        message_bytes = base64.b64decode(cloud_event.data['message']['data'])
        message_data = json.loads(message_bytes.decode('utf-8'))
        
        logger.info(f"Processing test failure: {message_data}")
        
        # Get test failure details from BigQuery
        test_result = get_test_failure_details(message_data.get('test_result_id'))
        
        if not test_result:
            logger.error(f"Test result not found: {message_data.get('test_result_id')}")
            return
        
        # Create JIRA defect (For Jira integration)
        defect_key = create_defect_in_jira(test_result)
        
        if defect_key:
            # Update test result with defect information
            update_test_result_with_defect(test_result['test_result_id'], defect_key)
            logger.info(f"Created JIRA defect: {defect_key}")
        
    except Exception as e:
        logger.error(f"Error creating JIRA defect: {str(e)}")
        raise

def get_test_failure_details(test_result_id):
    """
    Fetch test failure details from BigQuery
    """
    query = f"""
    SELECT 
        tr.test_result_id,
        tr.test_case_id,
        tr.expected_result,
        tr.actual_result,
        tr.failure_reason,
        tr.execution_timestamp,
        tc.test_name,
        tc.test_desc,
        tc.issue_id,
        i.issue_id,
        i.title as issue_title
    FROM `{PROJECT_ID}.{DATASET_ID}.test_results` tr
    JOIN `{PROJECT_ID}.{DATASET_ID}.test_cases` tc ON tr.test_case_id = tc.test_case_id
    JOIN `{PROJECT_ID}.{DATASET_ID}.issues` i ON tc.issue_id = i.issue_id
    WHERE tr.test_result_id = @test_result_id
    AND tr.status = 'FAILED'
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            # Class from the Google Cloud BigQuery client library for Python, used to define a single, named parameter that will be passed to a SQL query.
            bigquery.ScalarQueryParameter("test_result_id", "STRING", test_result_id)
        ]
    )
    
    # Send request to the BigQuery API to start a new query job using the query parameters defined in job_config
    # Obtain a QueryJob object in return to the query executed    
    query_job = get_bigquery_client().query(query, job_config=job_config)
    results = list(query_job)   # Wait for the job to complete and then fetch all the resulting rows into a list.
    
    if results:
        row = results[0]
        return {
            'test_result_id': row.test_result_id,
            'test_case_id': row.test_case_id,
            'test_name': row.test_name,
            'test_desc': row.test_desc,
            'expected_result': row.expected_result,
            'actual_result': row.actual_result,
            'failure_reason': row.failure_reason,
            'exec_timestamp': row.execution_timestamp,
            'issue_id': row.issue_id,
            'issue_title': row.issue_title
        }
    
    return None

def create_defect_in_jira(test_result):
    """
    Create a defect in JIRA based on test failure
    """
    try:
        # Prepare defect data
        summary = f"Test Failure: {test_result['test_name']}"

        # JIRA API v3 requires Atlassian Document Format (ADF) for rich text descriptions.
        description_adf = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Test Case: ", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": f"{test_result['test_name']}"}
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Test Description: ", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": f"{test_result['test_desc']}"}
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Related Requirement: ", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": f"{test_result['issue_id']} - {test_result['issue_title']}"}
                    ]
                },
                {"type": "rule"},
                {
                    "type": "heading", "attrs": {"level": 3},
                    "content": [{"type": "text", "text": "Failure Details"}]
                },
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem", "content": [{"type": "paragraph", "content": [
                                {"type": "text", "text": "Expected Result: ", "marks": [{"type": "strong"}]},
                                {"type": "text", "text": f"{test_result['expected_result']}"}
                            ]}]
                        },
                        {
                            "type": "listItem", "content": [{"type": "paragraph", "content": [
                                {"type": "text", "text": "Actual Result: ", "marks": [{"type": "strong"}]},
                                {"type": "text", "text": f"{test_result['actual_result']}"}
                            ]}]
                        },
                        {
                            "type": "listItem", "content": [{"type": "paragraph", "content": [
                                {"type": "text", "text": "Failure Reason: ", "marks": [{"type": "strong"}]},
                                {"type": "text", "text": f"{test_result['failure_reason']}"}
                            ]}]
                        },
                        {
                            "type": "listItem", "content": [{"type": "paragraph", "content": [
                                {"type": "text", "text": "Execution Time: ", "marks": [{"type": "strong"}]},
                                {"type": "text", "text": f"{test_result['exec_timestamp']}"}
                            ]}]
                        }
                    ]
                },
                {"type": "rule"},
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Test Case ID: ", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": f"{test_result['test_case_id']}"}
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Test Result ID: ", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": f"{test_result['test_result_id']}"}
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "This defect was automatically created by the Healthcare Testing System.", "marks": [{"type": "em"}]}]
                }
            ]
        }
        
        # JIRA issue data
        issue_data = {
            "fields": {
                "project": {"key": JIRA_PROJECT_KEY},
                "summary": summary,
                "description": description_adf,
                "issuetype": {"name": "Bug"},
                "priority": {"name": "High"},
                "labels": [
                    "automated-testing",
                    "healthcare-compliance",
                    "test-failure"
                ]
            }
        }
        
        # Create the issue
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        auth = (JIRA_USERNAME, JIRA_API_TOKEN)
        
        url = f"{JIRA_BASE_URL}/rest/api/3/issue"
        
        response = requests.post(
            url,
            headers=headers,
            auth=auth,
            data=json.dumps(issue_data)
        )
        
        response.raise_for_status()
        
        result = response.json()
        defect_key = result.get('key')
        
        # Link the defect to the original requirement
        if test_result.get('issue_id') and defect_key:
            link_issues(defect_key, test_result['issue_id'], "Relates")
        
        return defect_key
        
    except Exception as e:
        logger.error(f"Error creating JIRA defect: {str(e)}")
        return None

def link_issues(defect_key, requirement_key, link_type="Relates"):
    """
    Create a link between the defect and requirement in JIRA
    """
    try:
        link_data = {
            "type": {
                "name": link_type
            },
            "inwardIssue": {
                "key": defect_key
            },
            "outwardIssue": {
                "key": requirement_key
            },
            "comment": {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Automatically linked by Healthcare Testing System."
                                }
                            ]
                        }
                    ]
                }
            }
        }
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        auth = (JIRA_USERNAME, JIRA_API_TOKEN)
        
        url = f"{JIRA_BASE_URL}/rest/api/3/issueLink"
        
        response = requests.post(
            url,
            headers=headers,
            auth=auth,
            data=json.dumps(link_data)
        )
        
        response.raise_for_status()
        logger.info(f"Successfully linked {defect_key} to {requirement_key}")
        
    except Exception as e:
        logger.error(f"Error linking issues: {str(e)}")

def update_test_result_with_defect(test_result_id, defect_key):
    """
    Update test result in BigQuery with defect information
    """
    try:
        query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.test_results`
        SET 
            defect_id = @defect_key,
            defect_created_timestamp = @timestamp
        WHERE test_result_id = @test_result_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("defect_key", "STRING", defect_key),
                bigquery.ScalarQueryParameter("timestamp", "TIMESTAMP", datetime.utcnow().isoformat()),
                bigquery.ScalarQueryParameter("test_result_id", "STRING", test_result_id)
            ]
        )
        
        query_job = get_bigquery_client().query(query, job_config=job_config)
        query_job.result()     # Start the job and wait for it to complete and get the result.
        
        logger.info(f"Updated test result {test_result_id} with defect {defect_key}")
        
    except Exception as e:
        logger.error(f"Error updating test result: {str(e)}")

# After deploying, we need Google Cloud to provide a unique URL which will be invoked by any HTTP request (like a GET, POST, etc.)
# This decorator turns a standard Python function into a serverless web endpoint.
@functions_framework.http           # Register the below function as an HTTP-triggered Cloud Function.
def update_jira_from_test_results(request):
    """
    Manual function to sync test results back to JIRA
    Can be used for bulk updates or specific test results
    """
    try:
        request_json = request.get_json()
        test_result_ids = request_json.get('test_result_ids', [])
        
        if not test_result_ids:
            # Get all failed tests without defects
            query = f"""
            SELECT test_result_id
            FROM `{PROJECT_ID}.{DATASET_ID}.test_results`
            WHERE status = 'FAILED' 
            AND (defect_id IS NULL OR defect_id = '')
            ORDER BY execution_timestamp DESC
            LIMIT 100
            """
            
            query_job = get_bigquery_client().query(query)
            results = list(query_job)
            test_result_ids = [row.test_result_id for row in results]
        
        created_defects = []
        
        for test_result_id in test_result_ids:
            test_result = get_test_failure_details(test_result_id)
            if test_result:
                defect_key = create_defect_in_jira(test_result)
                if defect_key:
                    update_test_result_with_defect(test_result_id, defect_key)
                    created_defects.append(defect_key)
        
        return {
            'status': 'success',
            'created_defects': created_defects,
            'count': len(created_defects)
        }, 200
        
    except Exception as e:
        logger.error(f"Error in bulk defect creation: {str(e)}")
        return {'error': str(e)}, 500
