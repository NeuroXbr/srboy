#!/bin/bash

# SrBoy Deployment Script for Google Cloud Platform
# This script deploys the SrBoy application to Google Cloud Run

echo "🚀 SrBoy Deployment to Google Cloud Platform"
echo "============================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not found. Please install Google Cloud SDK."
    echo "   Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project configuration
PROJECT_ID="srboy-enterprise"
SERVICE_NAME="srboy-delivery"
REGION="us-central1"

echo "📋 Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   Service Name: $SERVICE_NAME"
echo "   Region: $REGION"
echo ""

# Confirm deployment
read -p "🤔 Do you want to proceed with deployment? (y/N): " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "❌ Deployment cancelled."
    exit 0
fi

echo ""
echo "🔧 Step 1: Setting up Google Cloud project..."
gcloud config set project $PROJECT_ID

echo ""
echo "🏗️ Step 2: Building and deploying with Cloud Build..."
gcloud builds submit --config cloudbuild.yaml --timeout=40m

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Step 3: Deployment completed successfully!"
    echo ""
    echo "🌐 Your SrBoy application is now live at:"
    gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"
    echo ""
    echo "📊 Service details:"
    gcloud run services describe $SERVICE_NAME --region=$REGION --format="table(status.conditions[0].type:label=STATUS,status.conditions[0].status:label=READY,spec.template.spec.containers[0].image:label=IMAGE)"
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Update DNS records to point to the Cloud Run URL"
    echo "2. Configure SSL certificate if using custom domain"
    echo "3. Monitor application logs: gcloud logs tail --follow --resource-type=cloud_run_revision --resource-name=$SERVICE_NAME"
    echo "4. Scale as needed: gcloud run services update $SERVICE_NAME --region=$REGION --max-instances=100"
else
    echo ""
    echo "❌ Deployment failed. Please check the logs above for details."
    echo ""
    echo "🔍 Troubleshooting steps:"
    echo "1. Check Cloud Build logs: gcloud builds log [BUILD_ID]"
    echo "2. Verify environment variables are correctly set"
    echo "3. Ensure database connectivity from Cloud Run"
    echo "4. Check service account permissions"
    exit 1
fi

echo ""
echo "📚 Additional Resources:"
echo "• Cloud Console: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME"
echo "• Documentation: https://cloud.google.com/run/docs"
echo "• Support: https://cloud.google.com/support"