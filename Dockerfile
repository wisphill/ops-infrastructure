FROM quay.io/argoproj/argocd:v2.11.3

USER root

# Install required packages
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    tar \
    nano \
    vim \
    bash \
    && rm -rf /var/lib/apt/lists/*

ENV SOPS_VERSION=3.12.1

RUN curl -fLO https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.linux.amd64 \
    && mv sops-v${SOPS_VERSION}.linux.amd64 /usr/local/bin/sops \
    && chmod +x /usr/local/bin/sops

# Install ksops (amd64)
ENV KSOPS_VERSION=4.4.0

RUN curl -fL https://github.com/viaduct-ai/kustomize-sops/releases/download/v${KSOPS_VERSION}/ksops_${KSOPS_VERSION}_Linux_x86_64.tar.gz \
    -o /tmp/ksops.tar.gz \
    && tar -xzf /tmp/ksops.tar.gz -C /tmp \
    && mv /tmp/ksops /usr/local/bin/ksops \
    && chmod +x /usr/local/bin/ksops \
    && rm /tmp/ksops.tar.gz

# Setup ksops plugin path
RUN mkdir -p /home/argocd/.config/kustomize/plugin/viaduct.ai/v1/ksops \
    && ln -s /usr/local/bin/ksops /home/argocd/.config/kustomize/plugin/viaduct.ai/v1/ksops/ksops \
    && chown -R 999:999 /home/argocd/.config

RUN /usr/local/bin/sops --version
RUN /usr/local/bin/ksops version || true

USER 999
