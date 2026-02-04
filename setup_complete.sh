#!/bin/bash

# =====================================================
# Complete Setup Script for Blog Planner Deployment
# =====================================================

echo "========================================="
echo "Blog Planner - Complete Setup"
echo "========================================="

# # STEP 1: Build Custom Jenkins
# echo ""
# echo "STEP 1: Building Custom Jenkins..."
# cd custom_jenkins
# docker build -t custom-jenkins:latest .
# cd ..
# echo "✅ Custom Jenkins built"

# # STEP 2: Start Jenkins
# echo ""
# echo "STEP 2: Starting Jenkins container..."
# docker stop jenkins-blog 2>/dev/null || true
# docker rm jenkins-blog 2>/dev/null || true

# docker run -d \
#   --name jenkins-blog \
#   -p 8080:8080 \
#   -p 50000:50000 \
#   -v jenkins_home:/var/jenkins_home \
#   -v /var/run/docker.sock:/var/run/docker.sock \
#   custom-jenkins:latest

# echo "Waiting for Jenkins to start (30 seconds)..."
# sleep 30

# echo "✅ Jenkins started"
# echo ""
# echo "Jenkins Admin Password:"
# docker exec jenkins-blog cat /var/jenkins_home/secrets/initialAdminPassword
# echo ""

# STEP 3: Enable Cloud Run API
echo ""
echo "STEP 3: Enabling Cloud Run API..."
gcloud auth activate-service-account --key-file=gen-lang-client-0068855436-6ac47f371465.json
gcloud config set project gen-lang-client-0068855436
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
echo "✅ Cloud Run enabled"

echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="

# ... end of your script ...
echo "Next Steps: ..."
read -p "Press enter to close..."