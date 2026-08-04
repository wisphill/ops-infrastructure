REGISTRY := ghcr.io/wisphill

ARGOCD_IMAGE := $(REGISTRY)/argocd-repo-server
TAG ?= latest
PLATFORM ?= linux/amd64

.PHONY: build-argocd push-argocd all

build-argocd:
	docker build \
		--platform $(PLATFORM) \
		-t $(ARGOCD_IMAGE):$(TAG) \
		.

push-argocd:
	docker push $(ARGOCD_IMAGE):$(TAG)

argocd: build-argocd push-argocd

all: argocd
