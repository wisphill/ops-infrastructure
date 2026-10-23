ARGOCD ?= argocd
ARGO ?= argo
KUBECTL ?= kubectl
NAMESPACE ?= argo-workflows
APP ?= argo-workflows
TEMPLATE ?= deploy-openmetadata-governance-portal-frontend
SOURCE_REVISION ?= main
PAGES_PROJECT ?= openmetadata-governance-portal
PAGES_BRANCH ?= main

.PHONY: app-status app-diff workflow-list workflow-status workflow-logs workflow-watch workflow-submit

# Read-only Argo CD and Argo Workflows status commands.
app-status:
	$(ARGOCD) app get $(APP)

app-diff:
	$(ARGOCD) app diff $(APP)

workflow-list:
	$(ARGO) list -n $(NAMESPACE)

workflow-status:
	test -n "$(WORKFLOW)"
	$(ARGO) get -n $(NAMESPACE) $(WORKFLOW)

workflow-logs:
	test -n "$(WORKFLOW)"
	$(ARGO) logs -n $(NAMESPACE) $(WORKFLOW) --follow

workflow-watch:
	test -n "$(WORKFLOW)"
	$(ARGO) watch -n $(NAMESPACE) $(WORKFLOW)

# This submits a real Cloudflare Pages deployment. Pass the public backend URL;
# it is embedded in the browser bundle and must not contain a secret.
workflow-submit:
	test -n "$(VITE_API_URL)"
	$(ARGO) submit -n $(NAMESPACE) --from workflowtemplate/$(TEMPLATE) \
		-p source-revision=$(SOURCE_REVISION) \
		-p pages-project=$(PAGES_PROJECT) \
		-p pages-branch=$(PAGES_BRANCH) \
		-p vite-api-url=$(VITE_API_URL) \
		--watch
