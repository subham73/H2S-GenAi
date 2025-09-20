# PowerShell Deployment Script for Windows
# Healthcare Testing System - JIRA-BigQuery Sync

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory=$true)]
    [string]$JiraBaseUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$JiraUsername,
    
    [Parameter(Mandatory=$true)]
    [string]$JiraApiToken,
    
    [Parameter(Mandatory=$true)]
    [string]$JiraProjectKey,
    
    [string]$Region = "us-central1",
    [string]$DatasetId = "healthcare_testing"
)

Write-Host "🚀 Deploying Healthcare Testing System..." -ForegroundColor Green

# Create Pub/Sub topics
Write-Host "📢 Creating Pub/Sub topics..." -ForegroundColor Yellow
try {
    gcloud pubsub topics create jira-updates --project=$ProjectId 2>$null
    gcloud pubsub topics create test-failures --project=$ProjectId 2>$null
    Write-Host "✅ Pub/Sub topics created" -ForegroundColor Green
} catch {
    Write-Host "ℹ️ Pub/Sub topics may already exist" -ForegroundColor Blue
}

# Deploy JIRA to BigQuery Cloud Function
Write-Host "🔄 Deploying JIRA to BigQuery sync function..." -ForegroundColor Yellow
Set-Location "cloud_functions\jira_to_bigquery"

gcloud functions deploy jira-to-bigquery `
  --gen2 `
  --runtime=python311 `
  --region=$Region `
  --source=. `
  --entry-point=jira_webhook_handler `
  --trigger=http `
  --allow-unauthenticated `
  --set-env-vars="GCP_PROJECT_ID=$ProjectId,BIGQUERY_DATASET_ID=$DatasetId,JIRA_BASE_URL=$JiraBaseUrl,JIRA_USERNAME=$JiraUsername,JIRA_API_TOKEN=$JiraApiToken" `
  --memory=512MB `
  --timeout=300s `
  --project=$ProjectId

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ JIRA to BigQuery function deployed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to deploy JIRA to BigQuery function" -ForegroundColor Red
    exit 1
}

# Deploy BigQuery to JIRA Cloud Function
Write-Host "🔙 Deploying BigQuery to JIRA sync function..." -ForegroundColor Yellow
Set-Location "..\bigquery_to_jira"

gcloud functions deploy bigquery-to-jira `
  --gen2 `
  --runtime=python311 `
  --region=$Region `
  --source=. `
  --entry-point=create_alm_defect `
  --trigger=topic=test-failures `
  --set-env-vars="GCP_PROJECT_ID=$ProjectId,BIGQUERY_DATASET_ID=$DatasetId,JIRA_BASE_URL=$JiraBaseUrl,JIRA_USERNAME=$JiraUsername,JIRA_API_TOKEN=$JiraApiToken,JIRA_PROJECT_KEY=$JiraProjectKey" `
  --memory=512MB `
  --timeout=300s `
  --project=$ProjectId

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ BigQuery to JIRA function deployed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to deploy BigQuery to JIRA function" -ForegroundColor Red
    exit 1
}

# Deploy manual sync function
Write-Host "🔄 Deploying manual sync function..." -ForegroundColor Yellow
gcloud functions deploy manual-jira-sync `
  --gen2 `
  --runtime=python311 `
  --region=$Region `
  --source="..\jira_to_bigquery" `
  --entry-point=sync_all_issues `
  --trigger=http `
  --allow-unauthenticated `
  --set-env-vars="GCP_PROJECT_ID=$ProjectId,BIGQUERY_DATASET_ID=$DatasetId,JIRA_BASE_URL=$JiraBaseUrl,JIRA_USERNAME=$JiraUsername,JIRA_API_TOKEN=$JiraApiToken" `
  --memory=1GB `
  --timeout=540s `
  --project=$ProjectId

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Manual sync function deployed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to deploy manual sync function" -ForegroundColor Red
    exit 1
}

Set-Location "..\..\"

# Get function URLs
Write-Host "📋 Getting function URLs..." -ForegroundColor Yellow
$webhookUrl = gcloud functions describe jira-to-bigquery --region=$Region --project=$ProjectId --format="value(serviceConfig.uri)"
$manualSyncUrl = gcloud functions describe manual-jira-sync --region=$Region --project=$ProjectId --format="value(serviceConfig.uri)"

Write-Host ""
Write-Host "✅ Deployment completed!" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 Configure JIRA webhook with this URL:" -ForegroundColor Cyan
Write-Host $webhookUrl -ForegroundColor White
Write-Host ""
Write-Host "🔄 Manual sync URL (for initial setup):" -ForegroundColor Cyan
Write-Host $manualSyncUrl -ForegroundColor White
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Yellow
Write-Host "1. Configure JIRA webhook to point to: $webhookUrl"
Write-Host "2. Set webhook events: Issue Created, Issue Updated"
Write-Host "3. Run initial sync: Invoke-RestMethod -Uri '$manualSyncUrl' -Method Post"
Write-Host "4. Test the bidirectional sync"
Write-Host ""
Write-Host "🔐 Make sure to set up proper IAM permissions for the service accounts" -ForegroundColor Magenta

# Save URLs to file for reference
$configFile = "deployment_config.txt"
@"
JIRA Webhook URL: $webhookUrl
Manual Sync URL: $manualSyncUrl
Project ID: $ProjectId
Region: $Region
Dataset ID: $DatasetId
Deployment Date: $(Get-Date)
"@ | Out-File $configFile

Write-Host ""
Write-Host "📄 Configuration saved to: $configFile" -ForegroundColor Blue
