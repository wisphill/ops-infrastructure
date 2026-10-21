"""Apply access.yaml (policies, roles, bot role assignments) to OpenMetadata.

Usage: python sync_access.py <access.yaml>

Needs an admin JWT in $OM_ADMIN_BOT_TOKEN and the server URL in $OM_URL (default: in-cluster).
Policies and roles are upserted; missing bots are created; bots only gain roles, none is ever
removed.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import requests
import yaml

API = os.environ.get("OM_URL", "http://openmetadata.openmetadata.svc.cluster.local:8585").rstrip("/") + "/api/v1"
HEADERS = {"Authorization": f"Bearer {os.environ['OM_ADMIN_BOT_TOKEN']}"}


def call(method: str, path: str, missing_ok: bool = False, **kwargs) -> Optional[dict]:
    response = requests.request(method, API + path, headers={**HEADERS, **kwargs.pop("headers", {})}, timeout=30, **kwargs)
    if missing_ok and response.status_code == 404:
        return None
    if not response.ok:
        sys.exit(f"{method} {path} -> {response.status_code}: {response.text}")
    return response.json()


def ensure_bot(name: str, spec: dict) -> dict:
    """Return the bot user, creating the user (JWT, no expiry) and bot entity if missing.

    An existing bot is left as is: re-creating it would rotate its token.
    """
    user = call("GET", f"/users/name/{name}", missing_ok=True, params={"fields": "roles"})
    if user is None:
        user = call(
            "POST",
            "/users",
            json={
                "name": name,
                "email": f"{name}@open-metadata.org",
                "displayName": spec.get("displayName", name),
                "description": spec.get("description", ""),
                "isBot": True,
                "authenticationMechanism": {
                    "authType": "JWT",
                    "config": {"JWTTokenExpiry": "Unlimited"},
                },
            },
        )
        user.setdefault("roles", [])
        print(f"bot {name}: user created")
    elif not user.get("isBot"):
        sys.exit(f"user {name} exists and is not a bot")
    if call("GET", f"/bots/name/{name}", missing_ok=True) is None:
        call(
            "POST",
            "/bots",
            json={
                "name": name,
                "displayName": spec.get("displayName", name),
                "description": spec.get("description", ""),
                "botUser": name,
            },
        )
        print(f"bot {name}: bot entity created")
    return user


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    definition = yaml.safe_load(Path(sys.argv[1]).read_text())

    for policy in definition.get("policies", []):
        call("PUT", "/policies", json=policy)
        print(f"policy {policy['name']}: applied")

    for role in definition.get("roles", []):
        call("PUT", "/roles", json=role)
        print(f"role {role['name']}: applied")

    for bot, spec in definition.get("bots", {}).items():
        user = ensure_bot(bot, spec)
        have = {r["name"] for r in user.get("roles") or []}
        patch = []
        for name in spec.get("roles", []):
            if name not in have:
                role = call("GET", f"/roles/name/{name}")
                patch.append({"op": "add", "path": "/roles/-", "value": {"id": role["id"], "type": "role"}})
        if patch:
            call("PATCH", f"/users/{user['id']}", data=json.dumps(patch), headers={"Content-Type": "application/json-patch+json"})
        print(f"bot {bot}: {'added ' + ', '.join(p['value']['id'] for p in patch) if patch else 'roles up to date'}")


if __name__ == "__main__":
    main()
