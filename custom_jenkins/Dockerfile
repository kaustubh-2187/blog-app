FROM jenkins/jenkins:lts

USER root

# Install Python
RUN apt-get update && apt-get install -y python3 python3-venv python3-pip

# -----------------------------
# Install Docker CLI + Engine
# -----------------------------
RUN apt-get update && \
    apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/debian \
        trixie stable" \
        > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y \
        docker-ce \
        docker-ce-cli \
        containerd.io && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# -----------------------------
# Install Google Cloud SDK + kubectl
# -----------------------------
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
        | gpg --dearmor -o /etc/apt/keyrings/google-cloud.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/google-cloud.gpg] \
        https://packages.cloud.google.com/apt cloud-sdk main" \
        > /etc/apt/sources.list.d/google-cloud-sdk.list && \
    apt-get update && \
    apt-get install -y \
        google-cloud-sdk \
        kubectl \
        google-cloud-sdk-gke-gcloud-auth-plugin && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# -----------------------------
# Docker socket permissions
# -----------------------------
ARG DOCKER_GID=999
RUN groupadd -g ${DOCKER_GID} docker || true && \
    usermod -aG docker jenkins

# -----------------------------
# Back to Jenkins user
# -----------------------------
USER jenkins