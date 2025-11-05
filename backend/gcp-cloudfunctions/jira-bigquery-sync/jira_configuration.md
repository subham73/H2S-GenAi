# JIRA Configuration Guide

## Setting up JIRA Webhooks

### 1. Create Webhook in JIRA

1. Go to **JIRA Administration** → **System** → **Webhooks**
2. Click **Create a WebHook**
3. Configure the webhook:

```
Name: Healthcare Testing System Sync
Status: Enabled
URL: [Cloud Function URL from deployment]
Description: Sync requirements to BigQuery for healthcare testing
```

### 2. Webhook Events

Select these events to trigger the sync:
- ✅ **Issue Created**
- ✅ **Issue Updated**
- ✅ **Issue Deleted** (optional)

### 3. JQL Filter (Optional)

To only sync specific issue types:
```jql
project = YOUR_PROJECT_KEY AND issuetype in (Requirement, Story, Epic)
```

### 4. Webhook Security

For production environments:
1. Use HTTPS endpoints only
2. Configure webhook authentication
3. Validate webhook signatures

## JIRA API Token Setup

### 1. Generate API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token**
3. Label: `Healthcare Testing System`
4. Copy the generated token

### 2. Test API Connection

```powershell
# PowerShell test
$headers = @{
    'Authorization' = 'Basic ' + [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("your-email@company.com:your-api-token"))
    'Accept' = 'application/json'
}

Invoke-RestMethod -Uri "https://your-domain.atlassian.net/rest/api/3/myself" -Headers $headers
```

## JIRA Project Configuration

### 1. Issue Types

Ensure these issue types exist:
- **Requirement** (or Story/Epic)
- **Bug** (for defects)
- **Test Case** (optional)

### 2. Custom Fields (Optional)

Create custom fields for better tracking:
- `Test Case Count` (Number)
- `Compliance Status` (Select List)
- `BigQuery Sync Status` (Select List)

### 3. Workflow States

Recommended workflow states:
- **Open** → **In Progress** → **Testing** → **Done**
- **Reopened** (for defects)

## Link Configuration

### 1. Issue Link Types

Configure these link types:
- **relates to** (defect → requirement)
- **blocks** (requirement → requirement)
- **tests** (test case → requirement)

### 2. Epic Links

If using Epics or Features for requirements:
```jql
project = YOUR_PROJECT AND issuetype = Feature
```

## JQL Queries for Monitoring

### 1. Requirements Ready for Testing
```jql
project = YOUR_PROJECT 
AND issuetype = Feature 
AND status = "Ready for Testing"
ORDER BY priority DESC
```

### 2. Active Defects
```jql
project = YOUR_PROJECT 
AND issuetype = Bug 
AND status NOT IN (Resolved, Closed)
AND labels = "automated-testing"
ORDER BY created DESC
```

### 3. Compliance Issues
```jql
project = YOUR_PROJECT 
AND labels = "healthcare-compliance"
AND status != Done
ORDER BY priority DESC
```

## Webhook Payload Examples

### Issue Created Event
```json
{
  "timestamp": 1692123456789,
  "webhookEvent": "jira:issue_created",
  "issue": {
    "id": "12345",
    "key": "HEALTH-123",
    "fields": {
      "summary": "Patient data encryption requirement",
      "description": "All patient data must be encrypted at rest and in transit",
      "issuetype": {
        "name": "Requirement"
      },
      "priority": {
        "name": "High"
      },
      "status": {
        "name": "Open"
      }
    }
  }
}
```

### Issue Updated Event
```json
{
  "timestamp": 1692123456789,
  "webhookEvent": "jira:issue_updated",
  "issue": {
    "id": "12345",
    "key": "HEALTH-123",
    "fields": {
      "status": {
        "name": "In Progress"
      }
    }
  },
  "changelog": {
    "items": [
      {
        "field": "status",
        "from": "Open",
        "to": "In Progress"
      }
    ]
  }
}
```

## Troubleshooting

### 1. Webhook Not Firing

Check:
- Webhook URL is accessible
- JIRA has internet access to GCP
- Events are properly configured
- JQL filter is not too restrictive

### 2. Authentication Issues

Verify:
- API token is valid
- Username format is correct (email)
- Permissions are sufficient

### 3. Missing Data

Common issues:
- Field names in JIRA vs BigQuery mismatch
- Custom fields not accessible via API
- Issue type filtering too restrictive

### 4. Performance Issues

Solutions:
- Implement webhook queuing
- Use batch processing for bulk updates
- Add retry logic with exponential backoff
