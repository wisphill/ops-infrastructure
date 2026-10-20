"""Apply a classification definition file to OpenMetadata.

Usage: python sync_classifications.py <workflow.yaml> <classification.yaml>...

The OpenMetadata connection is read from `workflowConfig.openMetadataServerConfig` of the workflow
file, so this step and the auto-classification run share one configuration. Every classification
and tag in the definition files is upserted (PUT); tags that exist on the server but not in the file
are left alone, so Steward-created tags survive.
"""

import sys
from pathlib import Path

import yaml

from metadata.config.common import load_config_file
from metadata.generated.schema.api.classification.createClassification import (
    CreateClassificationRequest,
)
from metadata.generated.schema.api.classification.createTag import CreateTagRequest
from metadata.generated.schema.entity.classification.tag import Tag
from metadata.generated.schema.entity.services.connections.metadata.openMetadataConnection import (
    OpenMetadataConnection,
)
from metadata.ingestion.ometa.ometa_api import OpenMetadata


def keep_server_state(recognizers: list[dict], existing: Tag | None) -> list[dict]:
    """Carry over recognizer ids and exception lists already stored on the server.

    Exception lists hold Steward feedback ("not sensitive here"), which is data rather than
    configuration, so a PUT from the file must not wipe them. Reusing ids keeps recognizers stable
    across runs.
    """
    stored = {r.name.root: r for r in (existing.recognizers or [])} if existing else {}
    merged = []
    for recognizer in recognizers:
        current = stored.get(recognizer["name"])
        if current:
            recognizer = {
                **recognizer,
                "id": str(current.id.root),
                "exceptionList": [
                    e.model_dump(mode="json", exclude_none=True) for e in current.exceptionList or []
                ],
            }
        merged.append(recognizer)
    return merged


def sync(metadata: OpenMetadata, definition: dict) -> None:
    classification = CreateClassificationRequest.model_validate(definition["classification"])
    metadata.create_or_update(classification)
    name = classification.name.root
    print(f"classification {name}: applied")

    for tag in definition.get("tags", []):
        fqn = f"{name}.{tag['name']}"
        existing = metadata.get_by_name(entity=Tag, fqn=fqn, fields=["recognizers"])
        request = {**tag, "classification": name}
        if "recognizers" in tag:
            request["recognizers"] = keep_server_state(tag["recognizers"], existing)
        metadata.create_or_update(CreateTagRequest.model_validate(request))
        print(f"tag {fqn}: applied ({len(tag.get('recognizers', []))} recognizers)")


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
