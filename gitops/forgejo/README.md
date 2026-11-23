# Forgejo Google OIDC

Before committing or syncing this configuration, add the dedicated Forgejo
Google OAuth application's credentials to the encrypted Secret:

```sh
SOPS_AGE_KEY_FILE=sops-age-key.txt \
  sops edit gitops/forgejo/secrets/google-oidc.enc.yaml
```

Set `stringData.key` to the Google **Client ID** and `stringData.secret` to the
Google **Client Secret**. Do not commit either value outside this SOPS-encrypted
file.

Register this authorized redirect URI in the Google OAuth application:

```
https://forgejo.foolosophy.dev/user/oauth2/Google/callback
```

Public Forgejo registration remains disabled. The Google source will provision
only the token whose `email` claim equals `phi.pounce@gmail.com`.
