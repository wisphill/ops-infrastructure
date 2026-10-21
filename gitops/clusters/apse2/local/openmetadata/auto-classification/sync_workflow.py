"""Apply a governance workflow definition file to OpenMetadata.

Usage: python sync_workflow.py <workflow.yaml> <workflow-definition.yaml>...

The OpenMetadata connection is read from `workflowConfig.openMetadataServerConfig` of the workflow
file, as in sync_classifications.py. A definition is upserted (PUT) only when it differs from the
server copy: every update redeploys the workflow to the Flowable engine.
"""

import sys
from pathlib import Path

import yaml

from metadata.config.common import load_config_file
from metadata.generated.schema.entity.services.connections.metadata.openMetadataConnection import (
    OpenMetadataConnection,
)
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


def sync(metadata: OpenMetadata, definition: dict) -> None:
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
