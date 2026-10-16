# Portal

Minimal user portal: sign in with Google (Gmail), land on a home page showing who you are. Nothing else.

```text
portal/
├── backend/            # Go server: Google OIDC login, session cookies, serves web/
│   ├── main.go         # config + routes
│   ├── auth.go         # login / callback / logout handlers
│   └── session.go      # HMAC-signed cookie values
├── web/                # static pages (login, home)
├── .env.example
└── Dockerfile
```

## How login works

1. `GET /auth/login` generates `state`, `nonce` and a PKCE verifier, stores them in a short-lived signed
   `portal_login` cookie, and redirects to Google.
2. Google redirects back to `GET /auth/callback?code=...&state=...`. The backend checks `state`, exchanges
   the code (with the PKCE verifier) for tokens, and **verifies the ID token**: RS256 signature against
   Google's JWKS (fetched and cached from `https://www.googleapis.com/oauth2/v3/certs`), `iss`, `aud` = our
   client ID, `exp`, then `nonce` and `email_verified`.
3. The backend sets its own `portal_session` cookie (HttpOnly, SameSite=Lax, Secure on https, 8h), signed
   with HMAC-SHA256 using `SESSION_SECRET`. Every request to `/home` and `/api/me` re-verifies that signature.
4. `POST /auth/logout` clears the session.

| Route              | Description                                     |
|--------------------|-------------------------------------------------|
| `GET /`            | Login page (redirects to `/home` if signed in)  |
| `GET /home`        | Home page, requires session                     |
| `GET /api/me`      | Current user as JSON, `401` if not signed in    |
| `GET /auth/login`  | Start Google sign-in                            |
| `GET /auth/callback` | OAuth redirect target                         |
| `POST /auth/logout`| Sign out                                        |
| `GET /healthz`     | Liveness check                                  |

## Google Cloud setup

1. Google Cloud Console → **APIs & Services → OAuth consent screen**: configure it (External, add test users
   while in "Testing").
2. **Credentials → Create credentials → OAuth client ID**, type **Web application**.
3. Authorized redirect URI: `http://localhost:8080/auth/callback` (add your production
   `https://<host>/auth/callback` later).
4. Copy the client ID and secret into `.env`.

## Run locally

```bash
cd portal
cp .env.example .env        # fill in GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / SESSION_SECRET
cd backend
set -a && source ../.env && set +a
go run .
# open http://localhost:8080
```

Tests: `cd backend && go test ./...`

## Docker

```bash
cd portal
docker build -t portal .
docker run --rm -p 8080:8080 --env-file .env -e WEB_DIR=/web portal
```

Behind TLS / an ingress, set `BASE_URL=https://<host>` so the redirect URI matches and cookies are marked Secure.
