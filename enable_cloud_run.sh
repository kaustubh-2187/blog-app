#!/bin/bash

# Enable Google Cloud Run API
# MANUAL: No changes needed

PROJECT_ID="gen-lang-client-0068855436"
SERVICE_ACCOUNT="gen-lang-client-0068855436-6ac47f371465.json"

echo "Authenticating with GCP..."
gcloud auth activate-service-account --key-file=$SERVICE_ACCOUNT

echo "Setting project..."
gcloud config set project $PROJECT_ID

echo "Enabling Cloud Run API..."
gcloud services enable run.googleapis.com

echo "Enabling Container Registry API..."
gcloud services enable containerregistry.googleapis.com

echo "✅ Cloud Run is ready!"