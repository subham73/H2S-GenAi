# Healthcare Testing System - Implementation Guide
## JIRA-BigQuery Bidirectional Sync

This guide provides a complete solution for implementing bidirectional synchronization between JIRA and Google BigQuery for your healthcare test case monitoring and execution system.

## 🏗️ Architecture Overview

```
┌─────────────┐    Webhooks    ┌─────────────────┐    Pub/Sub    ┌─────────────────┐
│    JIRA     │ ──────────────► │ Cloud Functions │ ─────────────► │   BigQuery     │
│             │                │                 │               │                │
│ Requirements│ ◄────────────── │  jira-to-bq     │ ◄───────────── │  - requirements │
│ Defects     │    REST API    │  bq-to-jira     │   Queries     │  - test_cases   │
│             │                │                 │               │  - test_results │
└─────────────┘                └─────────────────┘               └─────────────────┘
                                        │
                                        ▼
                               ┌─────────────────┐
                               │   GCP Agents    │
                               │                 │
                               │ - Test Generator│
                               │ - Compliance    │
                               │ - Test Executor │
                               └─────────────────┘
```

## 🚀 Quick Start Implementation

### Step 1: Prerequisites

1. **GCP Project Setup**
   - Enable Cloud Functions API
   - Enable BigQuery API
   - Enable Pub/Sub API
   - Create service account with appropriate permissions

2. **JIRA Setup**
   - Generate API Token
   - Note your JIRA base URL and project key
   - Admin access to create webhooks

3. **Local Environment**
   - Install Google Cloud SDK
   - Install PowerShell (for Windows scripts)

### Step 2: Deploy the System

```powershell
# Clone/Navigate to the project directory
cd ".\backend\gcp-cloudfunctions\jira-bigquery-sync"

# Run deployment script
.\deploy.ps1 -ProjectId "your-gcp-project" `
           -JiraBaseUrl "https://yourcompany.atlassian.net" `
           -JiraUsername "your-email@company.com" `
           -JiraApiToken "your-jira-api-token" `
           -JiraProjectKey "HEALTH"
```

# Deploy through shell script
.\deploy.sh

### Step 3: Configure JIRA Webhook

1. Go to JIRA Administration → System → Webhooks
2. Create webhook with the URL from deployment output
3. Configure events: Issue Created, Issue Updated
4. Test the webhook

### Step 4: Initial Data Sync

```powershell
# Run initial sync to import existing requirements
Invoke-RestMethod -Uri "https://your-manual-sync-url" -Method Post
```

## 🔄 Sync Flows Explained

### JIRA → BigQuery (Requirements Sync)

1. **Trigger**: JIRA webhook on requirement create/update
2. **Process**: Cloud Function extracts requirement data
3. **Action**: Insert/Update in BigQuery requirements table
4. **Notification**: Pub/Sub message for agent processing

### BigQuery → JIRA (Defect Creation)

1. **Trigger**: Test execution failure detected
2. **Process**: Pub/Sub message with test failure details
3. **Action**: Cloud Function creates JIRA defect
4. **Link**: Defect linked to original requirement

## 📊 BigQuery vs PostgreSQL Decision

**Recommendation: Stick with BigQuery**

### Why BigQuery is Better for Your Use Case:

✅ **Analytics & Reporting**
- Built-in analytics for compliance reporting
- Easy integration with Data Studio for dashboards
- Time-series analysis for test execution trends

✅ **AI/ML Integration**
- Native integration with Vertex AI for agents
- BigQuery ML for predictive analytics
- Easy data export for model training

✅ **Scalability**
- Handles large volumes of test execution data
- Automatic scaling without management
- Cost-effective for analytical workloads

✅ **GCP Ecosystem**
- Seamless integration with Cloud Functions
- Built-in security and compliance features
- Native support for healthcare data standards

### When to Consider PostgreSQL (Cloud SQL):

❌ **Complex Transactions**: If you need ACID transactions
❌ **Real-time Operations**: Sub-second response requirements
❌ **Existing ORM Dependencies**: Heavy reliance on PostgreSQL-specific features

### Migration Path (If Needed):

For migration to PostgreSQL later:

```sql
-- Export from BigQuery
EXPORT DATA OPTIONS(
  uri='gs://your-bucket/healthcare_data/*.csv',
  format='CSV',
  overwrite=true,
  header=true
) AS
SELECT * FROM `your-project.healthcare_testing.requirements`;

-- Import to Cloud SQL PostgreSQL
gcloud sql import csv your-instance gs://your-bucket/healthcare_data/requirements.csv \
  --database=healthcare_testing \
  --table=requirements
```

## 🛠️ Implementation Details

### Cloud Functions Architecture

#### 1. JIRA to BigQuery Function
- **Trigger**: HTTP webhook from JIRA
- **Purpose**: Sync requirements and handle updates
- **Memory**: 512MB (scalable based on load)
- **Timeout**: 300s

#### 2. BigQuery to JIRA Function
- **Trigger**: Pub/Sub message (test failures)
- **Purpose**: Create defects for failed tests
- **Memory**: 512MB
- **Timeout**: 300s

#### 3. Manual Sync Function
- **Trigger**: HTTP (for initial setup)
- **Purpose**: Bulk sync existing JIRA issues
- **Memory**: 1GB (handles large datasets)
- **Timeout**: 540s

### Data Flow Security

```
┌─────────────┐     HTTPS      ┌─────────────────┐
│    JIRA     │ ──────────────► │ Cloud Function  │
│             │   (Webhook)    │                 │
└─────────────┘                │ + API Token     │
                               │ + IAM Auth      │
                               └─────────────────┘
                                        │
                                        ▼ Authenticated
                               ┌─────────────────┐
                               │   BigQuery      │
                               │ + Encryption    │
                               │ + Audit Logs    │
                               └─────────────────┘
```

## 🧪 Testing Strategy

### 1. Unit Testing
- Test each Cloud Function independently
- Mock JIRA API responses
- Validate BigQuery operations

### 2. Integration Testing
- End-to-end webhook to BigQuery flow
- JIRA defect creation from test failures
- Data consistency validation

### 3. Load Testing
- Concurrent webhook handling
- Bulk sync performance
- Rate limiting validation

### 4. Compliance Testing
- Data encryption verification
- Audit log completeness
- HIPAA compliance validation

## 📈 Monitoring & Alerting

### Cloud Function Monitoring
```powershell
# Set up monitoring alerts
gcloud functions logs read jira-to-bigquery --limit=50
gcloud functions logs read bigquery-to-jira --limit=50
```

### BigQuery Monitoring
- Track sync success rates
- Monitor data freshness
- Alert on failed syncs

### JIRA Integration Health
- Webhook success rates
- API quota usage
- Defect creation success

## 🔒 Security Best Practices

### 1. API Security
- Use JIRA API tokens (not passwords)
- Rotate tokens regularly
- Implement webhook signature validation

### 2. GCP Security
- Use service accounts with minimal permissions
- Enable audit logging
- Encrypt data at rest and in transit

### 3. Network Security
- Restrict Cloud Function access
- Use VPC connectors if needed
- Implement rate limiting

## 📋 Maintenance & Operations

### Daily Operations
1. Monitor sync health dashboard
2. Check for failed syncs requiring retry
3. Validate test execution flow

### Weekly Tasks
1. Review compliance reports
2. Update test case coverage
3. Performance optimization

### Monthly Tasks
1. Security review and token rotation
2. Cost optimization analysis
3. Backup and disaster recovery testing

## 🚨 Troubleshooting Guide

### Common Issues

#### 1. Webhook Not Receiving Events
- Check JIRA webhook configuration
- Verify Cloud Function URL accessibility
- Review JIRA audit logs

#### 2. BigQuery Sync Failures
- Check service account permissions
- Validate BigQuery dataset exists
- Review Cloud Function logs

#### 3. JIRA Defect Creation Failures
- Verify JIRA API permissions
- Check issue type configuration
- Validate required fields

#### 4. Performance Issues
- Monitor Cloud Function execution time
- Check BigQuery slot usage
- Optimize query performance

### Debugging Commands
```powershell
# Check Cloud Function logs
gcloud functions logs read jira-to-bigquery --limit=50

# Test BigQuery connectivity
gcloud query --project=your-project --use_legacy_sql=false "SELECT COUNT(*) FROM \`your-project.healthcare_testing.requirements\`"

# Test JIRA API
$headers = @{
    'Authorization' = 'Basic ' + [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("email:token"))
}
Invoke-RestMethod -Uri "https://your-domain.atlassian.net/rest/api/3/myself" -Headers $headers
```

## 🎯 Next Steps

After implementing the basic sync:

1. **Enhance with AI Agents**
   - Implement test case generation from requirements
   - Add compliance validation agents
   - Create automated test execution pipeline

2. **Advanced Features**
   - Real-time dashboards
   - Predictive analytics for test failures
   - Automated compliance reporting

3. **Scale & Optimize**
   - Implement caching strategies
   - Add batch processing for bulk operations
   - Optimize for high-volume environments


### Complete event flow   


## Automatic actions for creating jira through bigquery_to_jira function

1. An agent notifies on the trigger-topic "test-failures" where a test failure is detected.
1. The create_alm_defect function is invoked as a result of the notification to topic "test-failures".
2. It reads the test_result_id from the message.
3. It calls get_test_failure_details() to query BigQuery for all the details about that specific failure.
4. If the failure is found, it calls create_defect_in_jira() to create a new "Bug" issue in our JIRA project with all the relevant details.
5. Finally, it updates the test_results table in BigQuery with the key of the newly created JIRA defect.


## Automatic actions for creating bigquery requirement from jira webhooks using webhook handler
1. The jira_webhook_handler function is invoked.
2. If the event type is either issue_created or issue_updated, then handle_requirement_sync is invoked with issue metadata.
3. handle_requirement_sync handles syncing JIRA issue to BigQuery requirements table using a MERGE statement.
4. publish_requirement_update is invoked for publishing to the pub/sub topic 'jira-updates' 
5. The agents reading the requirement update can be notified on this jira-updates topic to get the next actions done like creating the test cases and executing them, or they can read on requirements table to see any updates and handle them accordingly.