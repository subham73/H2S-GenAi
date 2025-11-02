import functions_framework
import json
import logging
from google.cloud import bigquery
from google.cloud import pubsub_v1
import requests
from datetime import datetime
import os
from dateutil.parser import parse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.getenv('GCP_PROJECT_ID')
DATASET_ID = os.getenv('BIGQUERY_DATASET_ID', 'qa_dataset')
JIRA_BASE_URL = os.getenv('JIRA_BASE_URL')
JIRA_USERNAME = os.getenv('JIRA_USERNAME')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
PUBSUB_TOPIC_ID = "jira-updates"

# Lazily initialized clients to improve cold start times and prevent startup errors.
_bigquery_client = None
_publisher_client = None

def get_bigquery_client():
    global _bigquery_client
    if not _bigquery_client:
        _bigquery_client = bigquery.Client()
    return _bigquery_client

def get_publisher_client():
    global _publisher_client
    if not _publisher_client:
        _publisher_client = pubsub_v1.PublisherClient()
    return _publisher_client

@functions_framework.http
def jira_webhook_handler(request):
    """
    Handle ALM webhooks for issue updates
    Primary entry point for real-time updates from ALM applications into our Google Cloud environment.
    """
    try:
        # Parse webhook payload
        webhook_data = request.get_json()
        
        if not webhook_data:
            return {'error': 'No JSON payload'}, 400
            
        event_type = webhook_data.get('webhookEvent')
        issue = webhook_data.get('issue', {})
        
        logger.info(f"Received ALM webhook: {event_type}")
        
        # Process different event types
        if event_type in ['jira:issue_created', 'jira:issue_updated']:
            return handle_req_sync(issue)
        
        # Ignore other event types
        return {'status': 'ignored'}, 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {'error': str(e)}, 500

def handle_req_sync(issue):
    """
    Sync ALM issues to BigQuery issues table using a MERGE statement.
    """
    try:
        # Extract issue data
        issue_data = {
            'req_id': issue.get('key'), # Unique identifier for the requirement
            'req': issue.get('fields', {}).get('summary'), # The title of the requirement
            # The description might contain multiple regulations. We'll treat it as a single-element array for now.
            'regulations': [issue.get('fields', {}).get('description', '') or ''],
            'ts': datetime.utcnow().isoformat()
        }
        
        # Use a MERGE statement for an atomic and efficient "upsert" operation.
        query = f"""
        MERGE `{PROJECT_ID}.{DATASET_ID}.Requirement` T
        USING (SELECT @req_id AS req_id) S
        ON T.req_id = S.req_id
        WHEN MATCHED THEN
            UPDATE SET
                req = @req,
                regulations = @regulations,
                ts = @ts,
                req_id = @req_id
        WHEN NOT MATCHED THEN
            INSERT (req_id, req, regulations, ts)
            VALUES (@req_id, @req, @regulations, @ts)
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("req_id", "STRING", issue_data['req_id']),
                bigquery.ScalarQueryParameter("req", "STRING", issue_data['req']),
                bigquery.ArrayQueryParameter("regulations", "STRING", issue_data['regulations']),
                bigquery.ScalarQueryParameter("ts", "TIMESTAMP", issue_data['ts']),
            ]
        )
        
        client = get_bigquery_client()
        query_job = client.query(query, job_config=job_config)
        query_job.result()  # Wait for the job to complete
        
        # Publish to Pub/Sub for further processing
        publish_issue_update(issue_data)
        
        logger.info(f"Successfully synced requirement: {issue_data['req_id']}")
        return {'status': 'success', 'req_id': issue_data['req_id']}, 200

    except Exception as e:
        logger.error(f"Error syncing requirement: {str(e)}")
        return {'error': str(e)}, 500

def publish_issue_update(issue_data):
    """
    Publish issue update to Pub/Sub for agent processing
    """
    message_data = {
        'event_type': 'issue_updated',
        'req_id': issue_data['req_id'],
        'req': issue_data['req'],
        'regulations': issue_data['regulations'],
        'ts': issue_data['ts'],
    }
    
    # Convert message to bytes
    message_bytes = json.dumps(message_data).encode('utf-8')
    
    publisher = get_publisher_client()
    topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC_ID)

    # Publish message
    # The publish() method returns a future.
    future = publisher.publish(topic_path, data=message_bytes)
    logger.info(f"Published issue update to Pub/Sub: {future.result()}")   # Blocks execution until the publish operation is complete.

def parse_jira_date(date_string):
    """
    Parse JIRA date format to ISO format
    """
    if not date_string:
        return None
    
    try:
        # JIRA uses ISO format: 2023-12-01T10:30:00.000+0000
        # Convert to UTC timestamp
        parsed_date = parse(date_string)
        return parsed_date.isoformat()
    except Exception as e:
        logger.warning(f"Could not parse date {date_string}: {e}")
        return None

@functions_framework.http
def sync_all_issues(request):
    """
    Manual sync of all issues (for initial setup)
    """
    try:
        logger.info(f"Starting bulk sync from ALM project.")
        logger.info(f"Target BQ Project: {PROJECT_ID}, Dataset: {DATASET_ID}")
        
        # Fetch all issues from ALM apps (JIRA for now)
        jql = "project = HEALTHCARE and issuetype = Story"
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        auth = (JIRA_USERNAME, JIRA_API_TOKEN)
        
        url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
        params = {
            'jql': jql,
            'maxResults': 1000,
            'fields': 'key,summary,description,priority,status,assignee,created,updated,issuetype'
        }        
        response = requests.get(url, headers=headers, auth=auth, params=params)
        response.raise_for_status()
        
        data = response.json()
        issues = data.get('issues', [])
        
        synced_count = 0
        for issue in issues:
            handle_req_sync(issue)
            synced_count += 1
        
        return {
            'status': 'success',
            'synced_issues': synced_count
        }, 200
        
    except Exception as e:
        logger.error(f"Error in bulk sync: {str(e)}")
        return {'error': str(e)}, 500
