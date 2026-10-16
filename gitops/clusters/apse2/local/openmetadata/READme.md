# OpenMetadata (local cluster)

| Argo CD Application        | Content                       | Sync wave |
|----------------------------|-------------------------------|-----------|
| `openmetadata-dependencies`| MySQL + OpenSearch            | 0         |
| `openmetadata`             | Server + UI (`values.yaml`)   | 1         |
| `openmetadata-ingestion`   | Ingestion CronJobs            | 2         |

UI: https://openmetadata.opswork.io.vn (basic auth provider).

## Disable account registration (self signup)

New users must not be able to create their own account from the login page; accounts are created by
an admin only.

### Why this is a manual step

`values.yaml` sets `openmetadata.config.authentication.enableSelfSignup: false`
(env `AUTHENTICATION_ENABLE_SELF_SIGNUP`). OpenMetadata only reads the authentication config from
Helm/env on the **first** boot against an empty database; after that the config lives in the MySQL
`openmetadata_db` and later Helm/env changes are ignored
([open-metadata/OpenMetadata#26159](https://github.com/open-metadata/OpenMetadata/issues/26159)).

So:

- **Fresh install** (empty MySQL): the Helm value is applied automatically, nothing to do.
- **Existing install**: do one of the procedures below once. The setting then persists in the DB
  across pod restarts, Argo CD syncs and chart upgrades.

### Option A: Admin UI (recommended)

1. Open https://openmetadata.opswork.io.vn and sign in as an admin
   (bootstrap admin is `admin@open-metadata.org`; change its default password if not done yet:
   `Settings > Members > Admins`).
2. Go to `Settings > SSO`.
3. Set **Enable Self Signup** to **Disabled**.
4. Click **Save**.

### Option B: Reset the stored security config to the Helm values

Use this if the UI is unavailable or the saved auth config is broken. It deletes the auth config
from the DB so the server re-seeds it from `values.yaml` on the next start. Make sure `values.yaml`
with `enableSelfSignup: false` is already synced by Argo CD.

```bash
kubectl -n openmetadata exec -it deploy/openmetadata -- \
  /opt/openmetadata/bootstrap/openmetadata-ops.sh remove-security-config

kubectl -n openmetadata rollout restart deploy/openmetadata
kubectl -n openmetadata rollout status deploy/openmetadata
```

> Any auth settings that were changed only in the UI (not in `values.yaml`) are lost by this reset.

### Verify

1. Sign out (or open a private window) and load the login page: there must be no
   **Create Account** / **Sign up** link.
2. From the API:

   ```bash
   curl -s https://openmetadata.opswork.io.vn/api/v1/system/config/auth | jq .enableSelfSignup
   # false
   ```

### Creating users afterwards

Admins add users from `Settings > Members > Users > Add User` (set a password, or let the user reset
it if SMTP is configured).

### Re-enabling

Set **Enable Self Signup** back to **Enabled** in `Settings > SSO`, and set
`enableSelfSignup: true` in `values.yaml` so a future fresh install matches.
