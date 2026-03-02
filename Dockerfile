FROM quay.io/argoproj/argocd:v2.11.3

USER root

# Install sops
RUN apt-get update && apt-get install -y curl gnupg \
    && curl -L https://github.com/mozilla/sops/releases/latest/download/sops-linux-amd64 -o /usr/local/bin/sops \
    && chmod +x /usr/local/bin/sops

# Install ksops
RUN curl -L https://github.com/viaduct-ai/kustomize-sops/releases/latest/download/ksops-linux-amd64 \
    -o /usr/local/bin/ksops \
    && chmod +x /usr/local/bin/ksops

USER 999
