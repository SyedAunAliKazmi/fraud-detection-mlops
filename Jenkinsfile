pipeline {
    agent any

    environment {
        DOCKER_IMAGE        = "aun12/fraud-detection"
        DOCKER_TAG          = "${BUILD_NUMBER}"
        MLFLOW_TRACKING_URI = "file:${WORKSPACE}/mlruns"
        DATA_PATH           = "${WORKSPACE}/data/creditcard.csv"
        KUBECONFIG          = "/var/lib/jenkins/.kube/config"
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/SyedAunAliKazmi/fraud-detection-mlops.git'
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Download Dataset') {
            steps {
                withCredentials([file(credentialsId: 'kaggle-json', variable: 'KAGGLE_JSON')]) {
                    sh '''
                        mkdir -p ~/.kaggle
                        cp $KAGGLE_JSON ~/.kaggle/kaggle.json
                        chmod 600 ~/.kaggle/kaggle.json
                        mkdir -p data
                        if [ ! -f data/creditcard.csv ]; then
                            pip install kaggle --quiet
                            kaggle datasets download -d mlg-ulb/creditcardfraud -p data/ --unzip
                        fi
                        python3 -c "import pandas as pd; df=pd.read_csv('data/creditcard.csv'); print('Rows:', len(df))"
                    '''
                }
            }
        }

        stage('Train Model') {
            steps {
                sh '''
                    . venv/bin/activate
                    python src/train.py
                    ls -lh models/fraud_model.pkl
                '''
            }
        }

        stage('Test API') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/ -v --tb=short
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} ."
                sh "docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest"
            }
        }

        stage('Push to DockerHub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker push ${DOCKER_IMAGE}:${DOCKER_TAG}
                        docker push ${DOCKER_IMAGE}:latest
                    '''
                }
            }
        }

        stage('Terraform Init') {
            steps {
                dir('terraform') {
                    sh 'terraform init'
                }
            }
        }

        stage('Terraform Plan') {
            steps {
                dir('terraform') {
                    sh "terraform plan -var='docker_image=${DOCKER_IMAGE}:${DOCKER_TAG}'"
                }
            }
        }

        stage('Terraform Apply') {
            steps {
                dir('terraform') {
                    sh "terraform apply -auto-approve -var='docker_image=${DOCKER_IMAGE}:${DOCKER_TAG}'"
                }
            }
        }

        stage('Verify Deployment') {
            steps {
                sh '''
                    kubectl rollout status deployment/fraud-detection -n fraud-detection --timeout=120s
                    kubectl get pods -n fraud-detection
                    kubectl get services -n fraud-detection
                    echo "=== ReplicaSet ==="
                    kubectl get replicaset -n fraud-detection
                '''
            }
        }
    }

    post {
        success {
            echo '✓ Pipeline completed — Fraud Detection system deployed!'
        }
        failure {
            echo '✗ Pipeline failed — check logs above'
        }
        always {
            sh 'docker logout || true'
        }
    }
}
