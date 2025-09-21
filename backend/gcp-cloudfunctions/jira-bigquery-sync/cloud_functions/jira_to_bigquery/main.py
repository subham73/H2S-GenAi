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
DATASET_ID = os.getenv('BIGQUERY_DATASET_ID', 'healthcare_data')
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
            return handle_issue_sync(issue)
        
        # Ignore other event types
        return {'status': 'ignored'}, 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {'error': str(e)}, 500

def handle_issue_sync(issue):
    """
    Sync ALM issues to BigQuery issues table using a MERGE statement.
    """
    try:
        # Extract issue data
        issue_data = {
            'issue_type': issue.get('fields', {}).get('issuetype', {}).get('name'),
            'issue_id': issue.get('key'),
            'title': issue.get('fields', {}).get('summary'),
            'description': issue.get('fields', {}).get('description'),
            'priority': issue.get('fields', {}).get('priority', {}).get('name'),
            'status': issue.get('fields', {}).get('status', {}).get('name'),
            'assignee': issue.get('fields', {}).get('assignee', {}).get('displayName') if issue.get('fields', {}).get('assignee') else None,
            'created_date': parse_jira_date(issue.get('fields', {}).get('created')),
            'updated_date': parse_jira_date(issue.get('fields', {}).get('updated')),
            'sync_timestamp': datetime.utcnow().isoformat()
        }
        
        # Use a MERGE statement for an atomic and efficient "upsert" operation.
        query = f"""
        MERGE `{PROJECT_ID}.{DATASET_ID}.issues` T
        USING (SELECT @issue_id AS issue_id) S
        ON T.issue_id = S.issue_id
        WHEN MATCHED THEN
            UPDATE SET
                issue_type = @issue_type,
                title = @title,
                description = @description,
                priority = @priority,
                status = @status,
                assignee = @assignee,
                updated_date = @updated_date,
                sync_timestamp = @sync_timestamp,
                issue_id = @issue_id
        WHEN NOT MATCHED THEN
            INSERT (issue_id, issue_type, title, description, priority, status, assignee, created_date, updated_date, sync_timestamp)
            VALUES (@issue_id, @issue_type, @title, @description, @priority, @status, @assignee, @created_date, @updated_date, @sync_timestamp)
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("issue_id", "STRING", issue_data['issue_id']),
                bigquery.ScalarQueryParameter("issue_type", "STRING", issue_data['issue_type']),
                bigquery.ScalarQueryParameter("title", "STRING", issue_data['title']),
                bigquery.ScalarQueryParameter("description", "STRING", issue_data['description']),
                bigquery.ScalarQueryParameter("priority", "STRING", issue_data['priority']),
                bigquery.ScalarQueryParameter("status", "STRING", issue_data['status']),
                bigquery.ScalarQueryParameter("assignee", "STRING", issue_data['assignee']),
                bigquery.ScalarQueryParameter("created_date", "TIMESTAMP", issue_data['created_date']),
                bigquery.ScalarQueryParameter("updated_date", "TIMESTAMP", issue_data['updated_date']),
                bigquery.ScalarQueryParameter("sync_timestamp", "TIMESTAMP", issue_data['sync_timestamp']),
            ]
        )
        
        client = get_bigquery_client()
        query_job = client.query(query, job_config=job_config)
        query_job.result()  # Wait for the job to complete
        
        # Publish to Pub/Sub for further processing
        publish_issue_update(issue_data)
        
        logger.info(f"Successfully synced issue: {issue_data['issue_id']}")
        return {'status': 'success', 'issue_id': issue_data['issue_id']}, 200

    except Exception as e:
        logger.error(f"Error syncing issue: {str(e)}")
        return {'error': str(e)}, 500

def publish_issue_update(issue_data):
    """
    Publish issue update to Pub/Sub for agent processing
    """
    message_data = {
        'event_type': 'issue_updated',
        'issue_id': issue_data['issue_id'],
        'issue_type': issue_data['issue_type'],
        'title': issue_data['title'],
        'description': issue_data['description'],
        'timestamp': issue_data['sync_timestamp']
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
        jql = "project = HEALTHCARE"
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        auth = (JIRA_USERNAME, JIRA_API_TOKEN)
        
        url = f"{JIRA_BASE_URL}/rest/api/3/search"
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
            handle_issue_sync(issue)
            synced_count += 1
        
        return {
            'status': 'success',
            'synced_issues': synced_count
        }, 200
        
    except Exception as e:
        logger.error(f"Error in bulk sync: {str(e)}")
        return {'error': str(e)}, 500
