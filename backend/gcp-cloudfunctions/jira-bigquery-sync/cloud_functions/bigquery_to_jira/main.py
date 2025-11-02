import functions_framework
import json
import logging
from google.cloud import bigquery
import requests
from datetime import datetime
import os 
import base64
from requests.auth import HTTPBasicAuth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.getenv('GCP_PROJECT_ID')
DATASET_ID = os.getenv('BIGQUERY_DATASET_ID', 'qa_dataset')
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
    Creates or updates a JIRA defect based on an issue_id from a Pub/Sub message.
    Triggered by Pub/Sub messages from test execution failures
    """
    try:
        logger.info("Pub/Sub message received for defect creation.")

        # Decode the Pub/Sub message data
        if 'data' not in cloud_event.data.get('message', {}):
            logger.warning("Pub/Sub message is missing the 'data' field.")
            return "No data in Pub/Sub message.", 200

        message_data_bytes = base64.b64decode(cloud_event.data['message']['data'])
        message_data = json.loads(message_data_bytes.decode('utf-8'))
        logger.info(f"Decoded message data: {message_data}")

        # Extract the issue_id from the message
        issue_id = message_data.get("issue_id")
        if not issue_id:
            logger.error("Could not determine issue_id from the Pub/Sub message.")
            return "Error: issue_id not found in message.", 400

        # Get issue details from BigQuery
        issue_details = get_issue_details(issue_id)

        if not issue_details:
            logger.error(f"Issue details not found for issue_id: {issue_id}")
            return "Issue details not found.", 404

        existing_defect_key = issue_details.get('jira_defect_key')

        if existing_defect_key:
            # This is an update event for an issue that already has a defect.
            logger.info(f"Issue {issue_id} already has defect {existing_defect_key}. Updating it.")
            update_defect_in_jira(existing_defect_key, issue_details)
        else:
            # This is a new issue or an updated issue that doesn't have a defect yet.
            logger.info(f"Creating new JIRA defect for issue_id: {issue_id}")
            defect_key = create_defect_in_jira(issue_details)
            
            if defect_key:
                # Update the BigQuery row with the new JIRA defect key.
                update_issue_with_defect(issue_id, defect_key)
                logger.info(f"Successfully created JIRA defect {defect_key} for issue {issue_id}")
        
    except Exception as e:
        logger.error(f"Error creating JIRA defect: {str(e)}")
        raise

def get_issue_details(issue_id):
    """
    Fetch issue details from BigQuery based on issue_id.
    """
    query = f"""
    SELECT 
        i.issue_id,
        i.test_id,
        i.ts,
        i.regulatory_tag,
        i.compliance_score,
        i.jira_defect_key,
        i.notes,
        tc.testcase_details,
        r.req_id,
        r.req as req_title,
        r.alm_id
    FROM `{PROJECT_ID}.{DATASET_ID}.Issue` i
    JOIN `{PROJECT_ID}.{DATASET_ID}.TestCase` tc ON i.test_id = tc.test_id
    JOIN `{PROJECT_ID}.{DATASET_ID}.Requirement` r ON tc.req_id = r.req_id
    WHERE i.issue_id = @issue_id
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            # Class from the Google Cloud BigQuery client library for Python, used to define a single, named parameter that will be passed to a SQL query.
            bigquery.ScalarQueryParameter("issue_id", "STRING", issue_id)
        ]
    )
    
    # Send request to the BigQuery API to start a new query job using the query parameters defined in job_config
    # Obtain a QueryJob object in return to the query executed    
    query_job = get_bigquery_client().query(query, job_config=job_config)
    results = list(query_job)   # Wait for the job to complete and then fetch all the resulting rows into a list.
    
    if results:
        row = results[0]
        return {
            'issue_id': row.issue_id,
            'test_id': row.test_id,
            'timestamp': row.ts,
            'regulatory_tag': row.regulatory_tag,
            'compliance_score': row.compliance_score,
            'jira_defect_key': row.jira_defect_key,
            'notes': row.notes,
            'testcase_details': row.testcase_details,
            'req_id': row.req_id,
            'req_title': row.req_title,
            'alm_id': row.alm_id
        }
    
    return None

def create_defect_in_jira(issue_details):
    """
    Create a defect in JIRA based on issue details.
    """
    try:
        # Prepare defect data
        summary = f"Compliance Issue Detected: {issue_details['req_title']}"
        description_adf = _build_jira_description_adf(issue_details)

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
                    "bq-issue"
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
        defect_key = result.get("key")
        
        # Link the defect to the original requirement. Remember to link it with alm_id (jira key) instead of req_id (bq key)
        if issue_details.get('alm_id') and defect_key:
            link_issues(defect_key, issue_details['alm_id'], "Relates")
        else:
            logger.info(f"There doesn't exist actual requirement with key {issue_details['alm_id']} in ALM instance to link to defect {defect_key}")
        
        return defect_key
        
    except Exception as e:
        logger.error(f"Error creating JIRA defect: {str(e)}")
        return None

def update_defect_in_jira(defect_key, issue_details):
    """
    Update an existing defect in JIRA.
    """
    """Update an existing defect in JIRA."""
    try:
        summary = f"Compliance Issue Detected: {issue_details['req_title']}"
        description_adf = _build_jira_description_adf(issue_details)
        # Check if the defect exists before trying to update it
        check_url = f"{JIRA_BASE_URL}/rest/api/3/issue/{defect_key}?fields=id"
        auth = (JIRA_USERNAME, JIRA_API_TOKEN)
        headers = {'Accept': 'application/json'}
        
        check_response = requests.get(check_url, headers=headers, auth=auth)
        
        if check_response.status_code == 404:
            logger.warning(f"JIRA defect {defect_key} not found. A new one will be created.")
            # Returning False will signal the calling logic to create a new defect.
            # This is a more robust way to handle missing defects.
            return False
        
        check_response.raise_for_status()

        # If the defect exists, proceed with the update
        summary = f"Compliance Issue Updated: {issue_details['req_title']}"
        description_adf = _build_jira_description_adf(issue_details, is_update=True)

        # Add a comment to the JIRA issue indicating it was updated
        comment_adf = {
            "body": {
                "type": "doc", "version": 1, "content": [
                    {"type": "paragraph", "content": [
                        {"type": "text", "text": "This issue has been automatically updated by the Healthcare Testing System with the latest details from BigQuery."}
                    ]}
                ]
            }
        }

        # JIRA update data
        issue_data = {
            "fields": {
                "summary": summary,
                "description": description_adf
            }
        }

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        auth = (JIRA_USERNAME, JIRA_API_TOKEN)
        # Update the issue fields
        url = f"{JIRA_BASE_URL}/rest/api/3/issue/{defect_key}"

        response = requests.put(
            url,
            headers=headers,
            auth=auth,
            data=json.dumps(issue_data)
        )

        response.raise_for_status()

        # Add a comment about the update
        comment_url = f"{JIRA_BASE_URL}/rest/api/3/issue/{defect_key}/comment"
        requests.post(
            comment_url,
            headers=headers,
            auth=auth,
            data=json.dumps(comment_adf)
        )

        logger.info(f"Successfully updated JIRA defect: {defect_key}")
        return True

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"JIRA defect {defect_key} not found. A new one will be created.")
            # To handle this, we can clear the jira_defect_key in BQ and re-trigger,
            # but for now, we let the manual process handle it.
        else:
            logger.error(f"Error updating JIRA defect {defect_key}: {e.response.text}")
        logger.error(f"Error updating JIRA defect {defect_key}: {e.response.text}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while updating JIRA defect {defect_key}: {str(e)}")
    
    return False

def _build_jira_description_adf(issue_details):
    """Builds the Atlassian Document Format (ADF) for the JIRA issue description."""
    # Safely get values, providing a default if None
    def get_val(key):
        return issue_details.get(key, 'N/A')

    return {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "Related Requirement: ", "marks": [{"type": "strong"}]}, {"type": "text", "text": f"{get_val('req_id')} - {get_val('req_title')}"}]},
            {"type": "rule"},
            {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": "Issue Details"}]},
            {"type": "bulletList", "content": [
                {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Compliance Score: ", "marks": [{"type": "strong"}]}, {"type": "text", "text": f"{get_val('compliance_score')}"}]}]},
                {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Regulatory Tag: ", "marks": [{"type": "strong"}]}, {"type": "text", "text": f"{get_val('regulatory_tag')}"}]}]},
                {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Notes: ", "marks": [{"type": "strong"}]}, {"type": "text", "text": f"{get_val('notes')}"}]}]},
                {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Test Case Details: ", "marks": [{"type": "strong"}]}, {"type": "text", "text": f"{get_val('testcase_details')}"}]}]},
                {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Detection Timestamp: ", "marks": [{"type": "strong"}]}, {"type": "text", "text": f"{get_val('timestamp')}"}]}]}]},
            {"type": "rule"},
            {"type": "paragraph", "content": [{"type": "text", "text": "Test ID: ", "marks": [{"type": "strong"}]}, {"type": "text", "text": f"{get_val('test_id')}"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": "BigQuery Issue ID: ", "marks": [{"type": "strong"}]}, {"type": "text", "text": f"{get_val('issue_id')}"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": "This defect was automatically created/updated by the Healthcare Testing System.", "marks": [{"type": "em"}]}]}
        ]
    }

def link_issues(defect_key, requirement_key, link_type="Relates"):
    """
    Create a link between the defect and requirement in JIRA
    """
    try:
        # Use the specified link type. Ensure this link type (e.g., "Relates")
        # exists in the Jira instance. The name is case-sensitive.
        logger.info(f"Using Jira issue link type: '{link_type}'")

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
        
        auth = HTTPBasicAuth(JIRA_USERNAME, JIRA_API_TOKEN)
        
        url = f"{JIRA_BASE_URL}/rest/api/3/issueLink"
        
        response = requests.request(
            'POST',
            url,
            headers=headers,
            auth=auth,
            data=json.dumps(link_data)
        )
        
        response.raise_for_status()
        logger.info(f"Successfully linked {defect_key} to {requirement_key}")
        
    except Exception as e:
        logger.error(f"Error linking issues: {str(e)}")


def update_issue_with_defect(issue_id, defect_key):
    """
    Update the Issue table in BigQuery with the new JIRA defect key.
    """
    try:
        query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.Issue`
        SET 
            jira_defect_key = @defect_key,
            jira_defect_created_ts = @timestamp
        WHERE issue_id = @issue_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("defect_key", "STRING", defect_key),
                bigquery.ScalarQueryParameter("timestamp", "TIMESTAMP", datetime.utcnow().isoformat()),
                bigquery.ScalarQueryParameter("issue_id", "STRING", issue_id)
            ]
        )
        
        query_job = get_bigquery_client().query(query, job_config=job_config)
        query_job.result()
        
        logger.info(f"Updated issue {issue_id} with defect key {defect_key}")
        
    except Exception as e:
        logger.error(f"Error updating test result: {str(e)}")

# After deploying, we need Google Cloud to provide a unique URL which will be invoked by any HTTP request (like a GET, POST, etc.)
# This decorator turns a standard Python function into a serverless web endpoint.
@functions_framework.http           # Register the below function as an HTTP-triggered Cloud Function.
def update_jira_from_test_results(request):
    """HTTP-triggered function to manually create JIRA defects for issues
    that don't have one yet.
    """
    try:
        request_json = request.get_json(silent=True) or {}
        issue_ids = request_json.get('issue_ids', [])

        if not issue_ids:
            # If no specific IDs are provided, get all issues without a JIRA key
            query = f"""
            SELECT issue_id
            FROM `{PROJECT_ID}.{DATASET_ID}.Issue`
            WHERE jira_defect_key IS NULL
            ORDER BY ts DESC
            LIMIT 100
            """
            
            query_job = get_bigquery_client().query(query)
            results = list(query_job)
            issue_ids = [row.issue_id for row in results]
            logger.info(f"Found {len(issue_ids)} issues to process.")
        
        created_defects = []
        
        for issue_id in issue_ids:
            issue_details = get_issue_details(issue_id)
            if issue_details:
                # Check if a defect already exists to avoid duplicates
                if issue_details.get('jira_defect_key'):
                    logger.info(f"Issue {issue_id} already has a defect: {issue_details['jira_defect_key']}")
                    continue
                defect_key = create_defect_in_jira(issue_details)
                if defect_key:
                    update_issue_with_defect(issue_id, defect_key)
                    created_defects.append(defect_key)
        
        return {
            'status': 'success',
            'created_defects': created_defects,
            'count': len(created_defects)
        }, 200
        
    except Exception as e:
        logger.error(f"Error in bulk defect creation: {str(e)}")
        return {'error': str(e)}, 500


@functions_framework.cloud_event
def create_alm_requirement(cloud_event):
    """
    Creates or updates a JIRA issue based on a req_id from a Pub/Sub message.
    Triggered by messages on the 'requirement-updates' topic.
    """
    try:
        logger.info("Pub/Sub message received for requirement creation/update.")

        # Decode the Pub/Sub message data
        if 'data' not in cloud_event.data.get('message', {}):
            logger.warning("Pub/Sub message is missing the 'data' field.")
            return "No data in Pub/Sub message.", 200

        message_data_bytes = base64.b64decode(cloud_event.data['message']['data'])
        message_data = json.loads(message_data_bytes.decode('utf-8'))
        logger.info(f"Decoded message data: {message_data}")

        # Extract the req_id from the message
        req_id = message_data.get("req_id")
        if not req_id:
            logger.error("Could not determine req_id from the Pub/Sub message.")
            return "Error: req_id not found in message.", 400
        
        logger.info(f"Processing requirement sync for req_id: {req_id}")
        # The create_or_update function handles both creation and updates,
        # including updating BigQuery with the JIRA key.
        create_or_update_requirement_in_jira(req_id)

    except Exception as e:
        logger.error(f"Error processing requirement event: {str(e)}")
        raise


def get_requirement_details(req_id):
    """Fetch requirement details from BigQuery."""
    query = f"""
    SELECT req_id, req, regulations, ts, alm_id
    FROM `{PROJECT_ID}.{DATASET_ID}.Requirement`
    WHERE req_id = @req_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("req_id", "STRING", req_id)]
    )
    query_job = get_bigquery_client().query(query, job_config=job_config)
    results = list(query_job)
    if results:
        row = results[0]
        return {
            'req_id': row.req_id,
            'req': row.req,
            'regulations': row.regulations,
            'ts': row.ts,
            'alm_id': row.alm_id
        }
    return None

def create_or_update_requirement_in_jira(req_id, batch_update=False):
    """Creates or updates a requirement in JIRA."""
    requirement_details = get_requirement_details(req_id)
    if not requirement_details:
        logger.error(f"Requirement details not found for req_id: {req_id}")
        return None

    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    auth = (JIRA_USERNAME, JIRA_API_TOKEN)

    # JIRA API requires Atlassian Document Format (ADF) for rich text.
    description_adf = {
        "type": "doc", "version": 1, "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "Regulations:", "marks": [{"type": "strong"}]}]},
            {"type": "bulletList", "content": [
                {"type": "listItem", "content": [{"type": "paragraph", "content": [
                    {"type": "text", "text": reg}
                ]}]} for reg in requirement_details.get('regulations', [])
            ]},
            {"type": "rule"},
            {"type": "paragraph", "content": [
                {"type": "text", "text": f"BigQuery ID: {requirement_details['req_id']}"}
            ]},
            {"type": "paragraph", "content": [
                {"type": "text", "text": f"Last Sync: {requirement_details['ts']}"}
            ]}
        ]
    }

    issue_data = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": requirement_details['req'],
            "description": description_adf,
            "issuetype": {"name": "Story"}, # Assuming requirements are 'Story' in JIRA
        },
        "update": {}
    }

    # Check if an alm_id (Jira key) already exists.
    alm_id = requirement_details.get('alm_id')
    
    try:
        # If alm_id exists, try to UPDATE the existing Jira issue.
        if alm_id:
            logger.info(f"Requirement {req_id} has existing alm_id {alm_id}. Attempting to update.")
            url = f"{JIRA_BASE_URL}/rest/api/3/issue/{alm_id}"
            response = requests.put(url, headers=headers, auth=auth, data=json.dumps(issue_data))
            
            # If the issue was not found in Jira (stale alm_id), we'll fall through to the creation logic.
            if response.status_code == 404:
                logger.warning(f"Jira issue {alm_id} not found. Will create a new one.")
                alm_id = None # Reset alm_id to trigger creation
            else:
                response.raise_for_status()
                logger.info(f"Successfully updated requirement in JIRA: {alm_id}")
                return alm_id

        # If alm_id is None (either initially or after a 404), CREATE a new issue.
        if not alm_id:
            logger.info(f"Requirement {req_id} does not have an alm_id. Creating new issue in JIRA.")
            create_url = f"{JIRA_BASE_URL}/rest/api/3/issue"
            create_response = requests.post(create_url, headers=headers, auth=auth, data=json.dumps(issue_data))
            create_response.raise_for_status()
            
            new_issue_data = create_response.json()
            new_alm_id = new_issue_data.get('key')
            logger.info(f"Successfully created new JIRA requirement: {new_alm_id}")

            if not batch_update:
                # IMPORTANT: Update BigQuery with the new JIRA-generated key in the 'alm_id' column.
                update_query = f"""
                UPDATE `{PROJECT_ID}.{DATASET_ID}.Requirement`
                SET alm_id = @new_alm_id WHERE req_id = @req_id
                """
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("new_alm_id", "STRING", new_alm_id),
                        bigquery.ScalarQueryParameter("req_id", "STRING", req_id),
                    ]
                )
                get_bigquery_client().query(update_query, job_config=job_config).result()
                logger.info(f"Updated BigQuery requirement {req_id} with new alm_id: {new_alm_id}")
            
            return new_alm_id

    except Exception as e:
        logger.error(f"Error creating/updating JIRA requirement {req_id}: {str(e)}")
        return None

def create_update_jira_from_requirement(request):
    """
    Manual HTTP-triggered function to sync requirements from BigQuery to JIRA.
    Can be used for bulk updates or specific requirements.
    """
    try:
        request_json = request.get_json(silent=True) or {}
        req_ids = request_json.get('req_ids', [])

        if not req_ids:
            # If no specific IDs are provided, get all requirements
            # This could be a very large number, so we limit it.
            query = f"""
            SELECT req_id
            FROM `{PROJECT_ID}.{DATASET_ID}.Requirement`
            ORDER BY ts DESC
            LIMIT 100
            """
            query_job = get_bigquery_client().query(query)
            req_ids = [row.req_id for row in query_job]
            logger.info(f"Found {len(req_ids)} requirements to process for manual sync.")

        synced_requirements = []
        for req_id in req_ids:
            result_key = create_or_update_requirement_in_jira(req_id)
            if result_key:
                synced_requirements.append(result_key)

        return {
            'status': 'success',
            'synced_requirements': synced_requirements,
            'count': len(synced_requirements)
        }, 200

    except Exception as e:
        logger.error(f"Error in manual requirement sync: {str(e)}")
        return {'error': str(e)}, 500
