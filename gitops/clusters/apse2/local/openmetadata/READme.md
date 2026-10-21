# OpenMetadata (local cluster)

| Argo CD Application        | Content                       | Sync wave |
|----------------------------|-------------------------------|-----------|
| `openmetadata-dependencies`| MySQL + OpenSearch            | 0         |
| `openmetadata`             | Server + UI (`values.yaml`)   | 1         |
| `openmetadata-ingestion`   | Ingestion CronJobs            | 2         |
| `openmetadata-access`      | Bot policies/roles (`access/access.yaml`) | 3 |
| `openmetadata-auto-classification` | Auto-classification CronJob (tag suggestions) | 3 |

UI: https://openmetadata.opswork.io.vn (Google SSO, see [Google SSO](#google-sso)).

## Google SSO

`values.yaml` configures the `google` provider with the confidential OIDC flow. Admin is
`<initialAdmins>@<principalDomain>` (`fizz.uet@gmail.com`); only `gmail.com` accounts may log in, and
self signup stays off, so other users must be added by an admin first.

### Google OAuth client

In Google Cloud Console > APIs & Services > Credentials, create an OAuth client ID of type
**Web application** with:

- Authorized JavaScript origin: `https://openmetadata.opswork.io.vn`
- Authorized redirect URI: `https://openmetadata.opswork.io.vn/callback`

Then, from this directory, open the decrypted file in your editor and replace the two `xxx` values
under the `oidc-secrets` document (`openmetadata-oidc-client-id`, `openmetadata-oidc-client-secret`):

```bash
SOPS_AGE_KEY_FILE=../../../../../sops-age-key.txt sops edit secrets/secrets.enc.yaml
```

Also set the same client ID in `openmetadata.config.authentication.clientId` in `values.yaml`
(not a secret).

> `secrets.enc.yaml` holds several Secrets in one file, so use `sops edit`:
> - `sops set` only changes the **first** document (`mysql-secrets`).
> - Encrypting a document separately and pasting it in breaks the file: all documents share one data
>   key and MAC, and ksops fails with `cipher: message authentication failed`.

### Switching an existing install from basic auth

The auth config is only seeded on first boot (see below), so after Argo CD syncs the new values,
reset the stored config once with [Option A](#option-a-reset-the-stored-security-config-to-the-helm-values).
On restart the server creates the admin user from `initialAdmins`/`principalDomain`. The old
`admin@open-metadata.org` basic-auth user can no longer sign in. Bot tokens (`OM_ADMIN_BOT_TOKEN`,
ingestion bot) keep working because they are signed by OpenMetadata and still validated through the
`/api/v1/system/config/jwks` entry in `publicKeys`.

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

## Bot access (policies and roles)

`access/access.yaml` declares the bot policies, roles and bots. Add a policy, role or bot there and
push: Argo CD runs the `openmetadata-access-sync` Job on every sync. Missing bots are created (JWT,
no expiry); existing bots only gain roles.

The auto-classification CronJob runs as its own bot, `data-sensitivity-bot`
(`DataSensitivityBotRole`: read tables and sample data, manage the DataSensitivity classification
and `SuggestionTaskWorkflow`, create Suggestion tasks). `ingestion-bot` is not managed by
`access.yaml`.

### data-sensitivity-bot token

After the first sync has created the bot, copy its token from **Settings > Bots >
data-sensitivity-bot** (or regenerate it there) and, from this directory, store it as
`OM_DATA_SENSITIVITY_BOT_TOKEN` in `openmetadata-ingestion-secrets`:

```bash
pbpaste | tr -d '\n' | jq -Rs . | SOPS_AGE_KEY_FILE=../../../../../sops-age-key.txt \
  sops set --value-stdin secrets/secrets.enc.yaml '["stringData"]["OM_DATA_SENSITIVITY_BOT_TOKEN"]'
```

Commit and push. Until the key exists, `oracle-auto-classification` pods fail with
`CreateContainerConfigError`.

The Job needs an admin JWT (user's Access Token, or a bot with the Admin role), stored as
`OM_ADMIN_JWT_TOKEN` in `ingestion/secrets.enc.yaml`.

To create it, sign in as an admin, open the profile (avatar, top right) > **Access Token** >
**Generate New Token**, pick an expiry (`Unlimited` avoids rotation; otherwise rotate before it
expires) and copy the token. Then, from this directory, write it from the clipboard (macOS) without
it appearing in shell history or the process list:

```bash
pbpaste | tr -d '\n' | jq -Rs . | SOPS_AGE_KEY_FILE=../../../../../sops-age-key.txt \
  sops set --value-stdin ingestion/secrets.enc.yaml '["stringData"]["OM_ADMIN_BOT_TOKEN"]'
```

Commit and push: Argo CD re-renders `openmetadata-ingestion-secrets` and the next
`openmetadata-access` sync runs the Job with the token.
