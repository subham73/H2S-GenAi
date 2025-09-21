#!/bin/bash

# Healthcare Testing System - Deployment Script
# This script deploys the Cloud Functions for JIRA-BigQuery sync

set -e

# Load environment variables from .env file if it exists
if [ -f .env ]; then
  echo "Loading environment variables from .env file"
  set -a # automatically export all variables
  source .env
  set +a # stop automatically exporting
else
  echo "Note: .env file not found. Relying on exported environment variables."
fi

# Check for required variables
if [ -z "$GCP_PROJECT_ID" ] || [ -z "$REGION" ] || [ -z "$JIRA_API_TOKEN" ]; then
  echo "Error: Required environment variables are not set."
  echo "Please create a .env file or export them."
  exit 1
fi

echo "🚀 Deploying Healthcare Testing System..."

# Create Pub/Sub topics
echo "📢 Creating Pub/Sub topics..."
gcloud pubsub topics create jira-updates --project=$GCP_PROJECT_ID || true
gcloud pubsub topics create test-failures --project=$GCP_PROJECT_ID || true

# Deploy JIRA to BigQuery Cloud Function
echo "🔄 Deploying JIRA to BigQuery sync function..."
cd cloud_functions/jira_to_bigquery

gcloud functions deploy jira-to-bigquery \
  --gen2 \
  --runtime=python312 \
  --region=$REGION \
  --source=. \
  --entry-point=jira_webhook_handler \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=$GCP_PROJECT_ID,BIGQUERY_DATASET_ID=$BIGQUERY_DATASET_ID,JIRA_BASE_URL=$JIRA_BASE_URL,JIRA_USERNAME=$JIRA_USERNAME,JIRA_API_TOKEN=$JIRA_API_TOKEN" \
  --memory=512MB \
  --timeout=300s \
  --project=$GCP_PROJECT_ID

# Deploy BigQuery to JIRA Cloud Function
echo "🔙 Deploying BigQuery to JIRA sync function..."
cd ../bigquery_to_jira

# This function is deployed with --trigger-topic=test-failures. 
# This means that whenever a message is published to the test-failures Pub/Sub topic, Google Cloud will invoke this function,
# passing the message details inside the cloud_event object. Refer create_alm_defect function in main.py
gcloud functions deploy bigquery-to-jira \
  --gen2 \
  --runtime=python312 \
  --region=$REGION \
  --source=. \
  --entry-point=create_alm_defect \
  --trigger-topic=test-failures \
  --set-env-vars="GCP_PROJECT_ID=$GCP_PROJECT_ID,BIGQUERY_DATASET_ID=$BIGQUERY_DATASET_ID,JIRA_BASE_URL=$JIRA_BASE_URL,JIRA_USERNAME=$JIRA_USERNAME,JIRA_API_TOKEN=$JIRA_API_TOKEN,JIRA_PROJECT_KEY=$JIRA_PROJECT_KEY" \
  --memory=512MB \
  --timeout=300s \
  --project=$GCP_PROJECT_ID

# Deploy manual sync function
gcloud functions deploy manual-jira-sync \
  --gen2 \
  --runtime=python312 \
  --region=$REGION \
  --source=../jira_to_bigquery \
  --entry-point=sync_all_issues \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=$GCP_PROJECT_ID,BIGQUERY_DATASET_ID=$BIGQUERY_DATASET_ID,JIRA_BASE_URL=$JIRA_BASE_URL,JIRA_USERNAME=$JIRA_USERNAME,JIRA_API_TOKEN=$JIRA_API_TOKEN" \
  --memory=1GB \
  --timeout=540s \
  --project=$GCP_PROJECT_ID

cd ../..

# Get function URLs
echo "📋 Getting function URLs..."
WEBHOOK_URL=$(gcloud functions describe jira-to-bigquery --region=$REGION --project=$GCP_PROJECT_ID --format="value(serviceConfig.uri)")
MANUAL_SYNC_URL=$(gcloud functions describe manual-jira-sync --region=$REGION --project=$GCP_PROJECT_ID --format="value(serviceConfig.uri)")

echo "✅ Deployment completed!"
echo ""
echo "🔗 URL to Configure JIRA webhook with:"
echo "$WEBHOOK_URL"
echo ""
echo "🔄 Manual sync URL (for initial setup):"
echo "$MANUAL_SYNC_URL"
echo ""
echo "📝 Next steps:"
echo "1. JIRA webhook points to: $WEBHOOK_URL"
echo "2. Enabled webhook events: Issue Created, Issue Updated"
echo "3. Run initial sync: curl -X POST $MANUAL_SYNC_URL"
echo "4. Test the bidirectional sync"
echo ""
