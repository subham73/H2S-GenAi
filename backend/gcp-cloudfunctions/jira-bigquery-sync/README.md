# JIRA-BigQuery Bidirectional Sync System

## Architecture Overview

This system provides bidirectional synchronization between JIRA and Google BigQuery for healthcare test case management and execution.

### Components

1. **Cloud Functions**
   - `jira-to-bigquery`: Sync requirements from JIRA to BigQuery
   - `bigquery-to-jira`: Create defects in JIRA from test failures
   - `webhook-handler`: Handle JIRA webhooks for real-time sync

2. **BigQuery Tables**
   - `issues`: Store JIRA requirements and bugs (all the entire list of stories/bugs/features/requirements)
   - `test_cases`: Generated test cases
   - `test_results`: Execution results
   - `compliance_reports`: HIPAA validation results
   - `execution_matrix`: Test execution tracking

3. **Pub/Sub Topics**
   - `jira-updates`: Queue JIRA webhook events
   - `test-failures`: Queue failed tests for defect creation

### Sync Flow

#### JIRA → BigQuery
1. JIRA webhook triggers on requirement create/update
2. Cloud Function processes webhook
3. Requirement synced to BigQuery
4. GCP Agent generates test cases

#### BigQuery → JIRA
1. Test execution detects failure
2. Pub/Sub message triggers defect creation
3. Cloud Function creates JIRA defect
4. Links defect to original requirement

## Setup Instructions

1. Deploy Cloud Functions
2. Configure JIRA webhooks
3. Set up Pub/Sub topics
4. Configure IAM permissions
5. Test bidirectional sync
