pipeline {
    agent any

    environment {
        // Virtual environment directory
        VENV_DIR = 'venv'
        
        // GCP Project ID
        GCP_PROJECT = 'gen-lang-client-0068855436'
        
        // Path to gcloud CLI inside Jenkins container
        GCLOUD_PATH = '/var/jenkins_home/google-cloud-sdk/bin'
        
        // Cloud Run service name
        SERVICE_NAME = 'blog-planner'
        
        // Cloud Run region
        REGION = 'us-central1'
    }

    stages {
        stage("Clone from GitHub") {
            steps {
                script {
                    echo 'Cloning from GitHub...'
                    // MANUAL: Update URL to your GitHub repo
                    checkout scmGit(
                        branches: [[name: '*/main']], 
                        extensions: [], 
                        userRemoteConfigs: [[
                            credentialsId: 'github-token',  // Must match Jenkins credential ID
                            url: 'https://github.com/kaustubh-2187/blog-app.git'  // Your repo URL
                        ]]
                    )
                }
            }
        }

        stage("Setup Virtual Environment") {
            steps {
                script {
                    echo 'Setting up virtual environment...'
                    sh '''
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -e .
                    '''
                }
            }
        }


        stage("Build and Push to GCR") {
            steps {
                withCredentials([file(credentialsId: 'gcp-key', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    script {
                        echo 'Building and pushing Docker image to GCR...'
                        sh '''
                        export PATH=$PATH:${GCLOUD_PATH}
                        
                        # Authenticate with GCP
                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                        
                        # Set project
                        gcloud config set project ${GCP_PROJECT}
                        
                        # Configure Docker to use GCR
                        gcloud auth configure-docker --quiet
                        
                        # Build Docker image
                        docker build -t gcr.io/${GCP_PROJECT}/${SERVICE_NAME}:latest .
                        
                        # Push to Google Container Registry
                        docker push gcr.io/${GCP_PROJECT}/${SERVICE_NAME}:latest
                        '''
                    }
                }
            }
        }

        stage("Deploy to Cloud Run") {
            steps {
                withCredentials([
                    file(credentialsId: 'gcp-key', variable: 'GOOGLE_APPLICATION_CREDENTIALS'),
                    string(credentialsId: 'GROQ_API_KEY', variable: 'GROQ_KEY'),
                    string(credentialsId: 'TAVILY_API_KEY', variable: 'TAVILY_KEY'),
                    string(credentialsId: 'GOOGLE_API_KEY', variable: 'GOOGLE_KEY')
                ]) {
                    script {
                        echo 'Deploying to Google Cloud Run...'
                        sh '''
                        export PATH=$PATH:${GCLOUD_PATH}
                        
                        # Authenticate with GCP
                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                        
                        # Set project
                        gcloud config set project ${GCP_PROJECT}
                        
                        # Deploy to Cloud Run
                        gcloud run deploy ${SERVICE_NAME} \
                            --image=gcr.io/${GCP_PROJECT}/${SERVICE_NAME}:latest \
                            --platform=managed \
                            --region=${REGION} \
                            --allow-unauthenticated \
                            --port=8000 \
                            --memory=1Gi \
                            --cpu=1 \
                            --min-instances=0 \
                            --max-instances=10 \
                            --set-env-vars="GROQ_API_KEY=${GROQ_KEY},TAVILY_API_KEY=${TAVILY_KEY},GOOGLE_API_KEY=${GOOGLE_KEY}"
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline completed!'
        }
        success {
            echo '✅ Deployment successful!'
            echo 'Access your API at the Cloud Run URL shown above'
        }
        failure {
            echo '❌ Deployment failed!'
        }
    }
}