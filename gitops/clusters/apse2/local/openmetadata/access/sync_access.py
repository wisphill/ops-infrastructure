"""Apply access.yaml (policies, roles, bots, teams, users) to OpenMetadata.

Usage: python sync_access.py <access.yaml>

Needs an admin JWT in $OM_ADMIN_BOT_TOKEN and the server URL in $OM_URL (default: in-cluster).
Policies and roles are upserted. Bots, teams and users are created if missing; existing ones only
gain what this file lists (bot roles, team defaultRoles, user teams) except team defaultRoles,
which is kept in sync both ways. Nothing already there is ever removed, other than a team's
defaultRoles no longer listed.
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


def ensure_team(name: str, spec: dict) -> None:
    """Create the team if missing, then sync its defaultRoles to those listed in spec.

    Members are never touched here. Other fields (displayName, description, teamType, ...) are
    only set on creation: edit those in the UI afterwards if needed.
    """
    team = call("GET", f"/teams/name/{name}", missing_ok=True, params={"fields": "defaultRoles"})
    if team is None:
        team = call(
            "POST",
            "/teams",
            json={
                "name": name,
                "teamType": spec.get("teamType", "Group"),
                "displayName": spec.get("displayName", name),
                "description": spec.get("description", ""),
            },
        )
        print(f"team {name}: created")
    else:
        print(f"team {name}: already exists")

    have = {r["name"] for r in team.get("defaultRoles") or []}
    want = set(spec.get("defaultRoles", []))
    if have == want:
        print(f"team {name}: defaultRoles up to date")
        return
    # defaultRoles is a list of EntityReference ({"id": ..., "type": "role"}), not of bare ids.
    role_refs = [{"id": call("GET", f"/roles/name/{role_name}")["id"], "type": "role"} for role_name in want]
    # "add" on an existing top-level member overwrites it, same as "replace" would, but also
    # works when the team has no defaultRoles yet (then the field is absent, not an empty list,
    # and "replace" would fail with "path not found").
    call(
        "PATCH",
        f"/teams/{team['id']}",
        data=json.dumps([{"op": "add", "path": "/defaultRoles", "value": role_refs}]),
        headers={"Content-Type": "application/json-patch+json"},
    )
    print(f"team {name}: defaultRoles set to {sorted(want)}")


def ensure_user(name: str, spec: dict) -> None:
    """Create the (non-bot) user if missing, then add any team listed in spec they lack.

    Teams already on the user (set here on an earlier run, or in the UI) are never removed.
    Other fields (displayName, description, ...) are only set on creation.
    """
    user = call("GET", f"/users/name/{name}", missing_ok=True, params={"fields": "teams"})
    if user is None:
        user = call(
            "POST",
            "/users",
            json={
                "name": name,
                "email": spec["email"],
                "displayName": spec.get("displayName", name),
                "description": spec.get("description", ""),
            },
        )
        user.setdefault("teams", [])
        print(f"user {name}: created")
    elif user.get("isBot"):
        sys.exit(f"user {name} exists and is a bot")
    else:
        print(f"user {name}: already exists")

    have = {t["name"] for t in user.get("teams") or []}
    missing = [team_name for team_name in spec.get("teams", []) if team_name not in have]
    if not missing:
        print(f"user {name}: teams up to date")
        return
    patch = []
    for team_name in missing:
        team = call("GET", f"/teams/name/{team_name}")
        patch.append({"op": "add", "path": "/teams/-", "value": {"id": team["id"], "type": "team"}})
    call("PATCH", f"/users/{user['id']}", data=json.dumps(patch), headers={"Content-Type": "application/json-patch+json"})
    print(f"user {name}: added to {', '.join(missing)}")


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

    for team, spec in definition.get("teams", {}).items():
        ensure_team(team, spec)

    users = definition.get("users", [])
    seen = set()
    for spec in users:
        name = spec["name"]
        if name in seen:
            sys.exit(f"user {name}: listed more than once in {sys.argv[1]}")
        seen.add(name)
        ensure_user(name, spec)


if __name__ == "__main__":
    main()
