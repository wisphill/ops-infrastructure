"""Apply a governance workflow definition file to OpenMetadata.

Usage: python sync_workflow.py <workflow.yaml> <workflow-definition.yaml>...

The OpenMetadata connection is read from `workflowConfig.openMetadataServerConfig` of the workflow
file, as in sync_classifications.py. A definition is upserted (PUT) only when it differs from the
server copy: every update redeploys the workflow to the Flowable engine.
"""

import sys
from pathlib import Path
from urllib.parse import quote

import yaml

from metadata.config.common import load_config_file
from metadata.generated.schema.entity.services.connections.metadata.openMetadataConnection import (
    OpenMetadataConnection,
)
from metadata.ingestion.ometa.client import APIError
from metadata.ingestion.ometa.ometa_api import OpenMetadata

# Fields a PUT updates on an existing workflow (WorkflowDefinitionUpdater); the description of a
# seeded workflow is kept as is, so comparing it would redeploy on every run.
COMPARED_FIELDS = ("config", "trigger", "nodes", "edges")


def matches(desired, actual) -> bool:
    """True if `actual` holds every value of `desired`.

    The server fills in schema defaults (node input/output, branches, ...), so extra keys on its
    side are not a difference; list lengths must still agree so removed nodes or edges count.
    """
    if isinstance(desired, dict):
        return isinstance(actual, dict) and all(matches(v, actual.get(k)) for k, v in desired.items())
    if isinstance(desired, list):
        return (
            isinstance(actual, list)
            and len(desired) == len(actual)
            and all(matches(d, a) for d, a in zip(desired, actual))
        )
    return desired == actual


def resolve_candidates(metadata: OpenMetadata, definition: dict) -> None:
    """Turn each {type, fullyQualifiedName} assignee candidate into a full entity reference.

    The server rejects a candidate without an id ("query param id must not be null"), and ids
    differ per environment, so the definition file names users and teams and the ids are looked
    up here. The server stores the reference as sent: with only {id, type} the workflow page has
    no name to show and displays the raw id, so name, fullyQualifiedName and displayName are
    sent too.
    """
    for node in definition.get("nodes", []):
        assignees = (node.get("config") or {}).get("assignees") or {}
        resolved = []
        for candidate in assignees.get("candidates") or []:
            if candidate.get("id"):
                resolved.append(candidate)
                continue
            kind, fqn = candidate.get("type"), candidate.get("fullyQualifiedName")
            if kind not in ("user", "team") or not fqn:
                raise ValueError(
                    f"node {node['name']}: candidate needs type user|team and fullyQualifiedName,"
                    f" got {candidate}"
                )
            try:
                entity = metadata.client.get(f"/{kind}s/name/{quote(fqn, safe='')}")
            except APIError as error:
                raise ValueError(f"node {node['name']}: {kind} {fqn} not found") from error
            if not entity:
                raise ValueError(f"node {node['name']}: {kind} {fqn} not found")
            reference = {
                "id": entity["id"],
                "type": kind,
                "name": entity["name"],
                "fullyQualifiedName": entity.get("fullyQualifiedName") or entity["name"],
            }
            if entity.get("displayName"):
                reference["displayName"] = entity["displayName"]
            resolved.append(reference)
        if resolved:
            assignees["candidates"] = resolved


def sync(metadata: OpenMetadata, definition: dict) -> None:
    resolve_candidates(metadata, definition)
    name = definition["name"]
    current = metadata.client.get(f"/governance/workflowDefinitions/name/{name}")
    if current and all(matches(definition.get(f), current.get(f)) for f in COMPARED_FIELDS):
        print(f"workflow {name}: up to date")
        return
    metadata.client.put("/governance/workflowDefinitions", json=definition)
    print(f"workflow {name}: applied")


def main() -> None:
    workflow_path, *definition_paths = sys.argv[1:]
    if not definition_paths:
        sys.exit(__doc__)

    server_config = load_config_file(Path(workflow_path))["workflowConfig"]["openMetadataServerConfig"]
    metadata = OpenMetadata(OpenMetadataConnection.model_validate(server_config))
    for path in definition_paths:
        sync(metadata, yaml.safe_load(Path(path).read_text()))


if __name__ == "__main__":
    main()
