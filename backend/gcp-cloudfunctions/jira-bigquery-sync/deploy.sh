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
gcloud pubsub topics create requirement-updates --project=$GCP_PROJECT_ID || true
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

# This function is triggered by insert or update events in the BigQuery 'Issue' table.
# When data is inserted or updated in the table, Eventarc invokes this function.
# The event payload contains information about the change, which is used by create_alm_defect.
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

# Deploy manual defect creation function from the same directory
echo "🛠️ Deploying manual defect creation function..."
gcloud functions deploy manual-defect-creation \
  --gen2 \
  --runtime=python312 \
  --region=$REGION \
  --source=. \
  --entry-point=update_jira_from_test_results \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=$GCP_PROJECT_ID,BIGQUERY_DATASET_ID=$BIGQUERY_DATASET_ID,JIRA_BASE_URL=$JIRA_BASE_URL,JIRA_USERNAME=$JIRA_USERNAME,JIRA_API_TOKEN=$JIRA_API_TOKEN,JIRA_PROJECT_KEY=$JIRA_PROJECT_KEY" \
  --memory=1GB \
  --timeout=540s \
  --project=$GCP_PROJECT_ID

# Deploy BigQuery to JIRA Requirement Cloud Function
echo "🔙 Deploying BigQuery to JIRA requirement sync function..."
# This function is triggered by insert or update events in the BigQuery 'Requirement' table.
gcloud functions deploy bigquery-to-jira-requirement \
  --gen2 \
  --runtime=python312 \
  --region=$REGION \
  --source=. \
  --entry-point=create_alm_requirement \
  --trigger-topic=requirement-updates \
  --set-env-vars="GCP_PROJECT_ID=$GCP_PROJECT_ID,BIGQUERY_DATASET_ID=$BIGQUERY_DATASET_ID,JIRA_BASE_URL=$JIRA_BASE_URL,JIRA_USERNAME=$JIRA_USERNAME,JIRA_API_TOKEN=$JIRA_API_TOKEN,JIRA_PROJECT_KEY=$JIRA_PROJECT_KEY" \
  --memory=512MB \
  --timeout=300s \
  --project=$GCP_PROJECT_ID

# Deploy manual requirement creation function
echo "🛠️ Deploying manual requirement creation function..."
gcloud functions deploy manual-requirement-creation \
  --gen2 \
  --runtime=python312 \
  --region=$REGION \
  --source=. \
  --entry-point=create_update_jira_from_requirement \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=$GCP_PROJECT_ID,BIGQUERY_DATASET_ID=$BIGQUERY_DATASET_ID,JIRA_BASE_URL=$JIRA_BASE_URL,JIRA_USERNAME=$JIRA_USERNAME,JIRA_API_TOKEN=$JIRA_API_TOKEN,JIRA_PROJECT_KEY=$JIRA_PROJECT_KEY" \
  --memory=1GB \
  --timeout=540s \
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
MANUAL_DEFECT_URL=$(gcloud functions describe manual-defect-creation --region=$REGION --project=$GCP_PROJECT_ID --format="value(serviceConfig.uri)")
MANUAL_REQ_URL=$(gcloud functions describe manual-requirement-creation --region=$REGION --project=$GCP_PROJECT_ID --format="value(serviceConfig.uri)")

echo "✅ Deployment completed!"
echo ""
echo "🔗 URL to Configure JIRA webhook with:"
echo "$WEBHOOK_URL"
echo ""
echo "🔄 Manual JIRA->BQ sync URL (for initial setup):"
echo "$MANUAL_SYNC_URL"
echo ""
echo "🛠️ Manual BQ->JIRA defect creation URL (for reprocessing issues):"
echo "$MANUAL_DEFECT_URL"
echo ""
echo "🛠️ Manual BQ->JIRA requirement creation URL (for reprocessing requirements):"
echo "$MANUAL_REQ_URL"
echo ""
echo "📝 Next steps:"
echo "1. JIRA webhook points to: $WEBHOOK_URL"
echo "2. Enabled webhook events: Issue Created, Issue Updated"
echo "3. Run initial JIRA->BQ sync: curl -X POST $MANUAL_SYNC_URL"
echo "4. To manually create defects for issues without one, run: curl -X POST $MANUAL_DEFECT_URL"
echo "   (Pass {'issue_ids': ['id1']} to target specific issues)"
echo "5. To manually sync requirements from BQ to JIRA, run: curl -X POST $MANUAL_REQ_URL"
echo "   (Pass {'req_ids': ['REQ-1']} to target specific requirements)"
echo ""
