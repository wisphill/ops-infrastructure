# OpenMetadata Governance Portal backend

Argo CD deploys this FastAPI backend to the `governance-portal` namespace. NGINX
serves external requests for `governance-portal-api.foolosophy.dev` and forwards
them to the ClusterIP Service on port 80.

The backend image is built from the `main` branch of
`wisphill/openmetata-governance-portal` and pushed as
`docker-registry.docker-registry.svc.cluster.local:5000/governance-portal/backend:main`.
The tag is deliberately paired with `imagePullPolicy: Always`; the build workflow
only restarts the Deployment after an explicit approval.

## Required secret

Before the Application can become healthy, create the encrypted SOPS Secret named
`openmetadata-governance-portal-backend-secrets` in the `governance-portal`
namespace. It must provide the required backend settings, including:

- `SESSION_SECRET`
- `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, and `OIDC_REDIRECT_URI`
- `OPENMETADATA_BASE_URL` and `OM_ADMIN_BOT_TOKEN`
- `PORTAL_PUBLIC_URL`, `BACKEND_PUBLIC_URL`, and `CORS_ORIGINS`

Set `BACKEND_PUBLIC_URL` and `OIDC_REDIRECT_URI` to
`https://governance-portal-api.foolosophy.dev` (the latter with `/auth/callback`),
and set `CORS_ORIGINS` to the deployed frontend origin. Keep credentials encrypted
with the repository's SOPS/AGE convention; do not commit plaintext values.
