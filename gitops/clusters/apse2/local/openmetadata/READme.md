# OpenMetadata (local cluster)

| Argo CD Application        | Content                       | Sync wave |
|----------------------------|-------------------------------|-----------|
| `openmetadata-dependencies`| MySQL + OpenSearch            | 0         |
| `openmetadata`             | Server + UI (`values.yaml`)   | 1         |
| `openmetadata-ingestion`   | Ingestion CronJobs            | 2         |
| `openmetadata-auto-classification` | Auto-classification CronJob (tag suggestions) | 3 |

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

It cannot be done from the UI: `Settings > SSO` only lists SSO providers, each with its own
"Enable Self Signup" toggle, and has no entry for the basic (username/password) provider.

### Option A: Reset the stored security config to the Helm values

Deletes the auth config from the DB so the server re-seeds it from `values.yaml` on the next start.
Make sure `values.yaml` with `enableSelfSignup: false` is already synced by Argo CD.

```bash
kubectl -n openmetadata exec -it deploy/openmetadata -- \
  /opt/openmetadata/bootstrap/openmetadata-ops.sh remove-security-config

kubectl -n openmetadata rollout restart deploy/openmetadata
kubectl -n openmetadata rollout status deploy/openmetadata
```

> Any auth settings that were changed only in the UI (not in `values.yaml`) are lost by this reset.

### Option B: Edit only `enableSelfSignup` in the stored config

Keeps every other stored auth setting. Export the config, flip the flag, import it back:

```bash
kubectl -n openmetadata exec -it deploy/openmetadata -c openmetadata -- sh -c '
  OPS=/opt/openmetadata/bootstrap/openmetadata-ops.sh
  $OPS get-security-config -o /tmp/security.yaml &&
  sed -i "s/^  enableSelfSignup: true/  enableSelfSignup: false/" /tmp/security.yaml &&
  grep -n "enableSelfSignup" /tmp/security.yaml &&
  $OPS update-security-config -f /tmp/security.yaml &&
  rm -f /tmp/security.yaml'

kubectl -n openmetadata rollout restart deploy/openmetadata
```

`update-security-config` asks for confirmation; check the `grep` output shows
`enableSelfSignup: false` under `authenticationConfiguration` before confirming.

### Verify

1. Sign out (or open a private window) and load the login page: there must be no
   **Create Account** / **Sign up** link.
2. From the API (inside the pod; the public URL is behind a Cloudflare challenge):

   ```bash
   kubectl -n openmetadata exec deploy/openmetadata -c openmetadata -- \
     wget -qO- localhost:8585/api/v1/system/config/auth | jq .enableSelfSignup
   # false
   ```

   If this still says `true` while `printenv AUTHENTICATION_ENABLE_SELF_SIGNUP` in the pod says
   `false`, the DB copy was never updated: do Option A or B.

### Creating users afterwards

Admins add users from `Settings > Team & User Management > Users > Add User` (set a password, or let the user reset
it if SMTP is configured).

### Re-enabling

Set `enableSelfSignup: true` in `values.yaml`, let Argo CD sync, then run Option A (or Option B
with the `sed` reversed).
