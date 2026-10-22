"""Hand the approved "C1-C4 Đề xuất" proposal tags over to the data owners.

Usage: python request_owner_review.py <workflow.yaml>

The OpenMetadata connection is read from `workflowConfig.openMetadataServerConfig` of the workflow
file, as in sync_workflow.py.

run_auto_classification.py files a Suggestion task for a proposal tag ("DataSensitivity.C1 Đề
xuất" ... "C4 Đề xuất"); once a Data Steward approves it, the proposal tag sits on the column.
Every run of this script looks at all tables and, for each column carrying a proposal tag:

1. files a Suggestion task for the real tag (the same level without "Đề xuất"), reviewers: the
   table owners (admins if the table has none), following SuggestionTaskWorkflow;
2. removes the proposal tag from the column.

The task is filed before the tag is removed: if filing fails the tag stays and the next run tries
again, and an open task for the same column and level is never filed twice (so a failed removal
only costs a retry). The real tag is written to the column when the owner approves the task.
"""

import json
import sys
from pathlib import Path
from typing import Iterator

from metadata.config.common import load_config_file
from metadata.generated.schema.entity.services.connections.metadata.openMetadataConnection import (
    OpenMetadataConnection,
)
from metadata.ingestion.ometa.ometa_api import OpenMetadata
from metadata.utils.logger import ingestion_logger

logger = ingestion_logger()

CLASSIFICATION = "DataSensitivity"
PROPOSAL_SUFFIX = " Đề xuất"
LEVELS = ("C1", "C2", "C3", "C4")
PROPOSAL_TAGS = {f"{CLASSIFICATION}.{level}{PROPOSAL_SUFFIX}": level for level in LEVELS}
# Task statuses that no longer block filing a new task for the same column and tag.
CLOSED_STATUSES = {"Approved", "Rejected", "Expired"}


def iter_tables(metadata: OpenMetadata) -> Iterator[dict]:
    after = None
    while True:
        params = {"fields": "columns,tags,owners", "limit": 100}
        if after:
            params["after"] = after
        page = metadata.client.get("/tables", data=params) or {}
        yield from page.get("data", [])
        after = (page.get("paging") or {}).get("after")
        if not after:
            return


def open_task_keys(metadata: OpenMetadata, table_fqn: str) -> set[tuple[str, str]]:
    """(fieldPath, tagFQN) of the Suggestion tasks on the table that are still being reviewed."""
    keys, after = set(), None
    while True:
        params = {"type": "Suggestion", "aboutEntity": table_fqn, "fields": "payload", "limit": 100}
        if after:
            params["after"] = after
        page = metadata.client.get("/tasks", data=params) or {}
        for task in page.get("data", []):
            payload = task.get("payload") or {}
            if task.get("status") in CLOSED_STATUSES or payload.get("suggestionType") != "Tag":
                continue
            try:
                labels = json.loads(payload.get("suggestedValue") or "[]")
            except ValueError:
                continue
            keys.update((payload.get("fieldPath"), label.get("tagFQN")) for label in labels)
        after = (page.get("paging") or {}).get("after")
        if not after:
            return keys


def owner_names(table: dict) -> list[str]:
    """Owners (users or teams) as reviewers; empty means the workflow assigns the admins."""
    return [owner["name"] for owner in table.get("owners") or [] if owner.get("name")]


def file_owner_task(
    metadata: OpenMetadata, table: dict, column_name: str, real_fqn: str, reviewers: list[str]
) -> None:
    table_fqn = table["fullyQualifiedName"]
    suggestion = {
        "tagFQN": real_fqn,
        "source": "Classification",
        "labelType": "Generated",
        "state": "Confirmed",
        "reason": "Data Steward đã duyệt đề xuất; chờ Data Owner duyệt nhãn chính thức",
    }
    metadata.client.post(
        "/tasks",
        json={
            "type": "Suggestion",
            "category": "MetadataUpdate",
            "displayName": f"{real_fqn} cho {table['name']}.{column_name}",
            "about": f"<#E::table::{table_fqn}>",
            "assignees": reviewers,
            "reviewers": reviewers,
            "payload": {
                "suggestionType": "Tag",
                "fieldPath": f"columns.{column_name}.tags",
                "suggestedValue": json.dumps([suggestion]),
                "source": "AutoPilot",
                "reasoning": f'Đề xuất nhãn chính thức: cột "{column_name}" thành nhãn "{real_fqn}"',
            },
        },
    )


def remove_tags(metadata: OpenMetadata, table: dict, removals: list[tuple[int, int]]) -> None:
    """JSON-patch the proposal tags off the columns; highest tag index first within a column so
    the remaining indexes stay valid."""
    operations = [
        {"op": "remove", "path": f"/columns/{column_index}/tags/{tag_index}"}
        for column_index, tag_index in sorted(removals, reverse=True)
    ]
    metadata.client.patch(f"/tables/{table['id']}", data=json.dumps(operations))


def process_table(metadata: OpenMetadata, table: dict) -> int:
    removals: list[tuple[int, int]] = []
    candidates = []  # (column_index, tag_index, column_name, proposal_fqn)
    for column_index, column in enumerate(table.get("columns") or []):
        for tag_index, tag in enumerate(column.get("tags") or []):
            if tag.get("tagFQN") in PROPOSAL_TAGS:
                candidates.append((column_index, tag_index, column["name"], tag["tagFQN"]))
    if not candidates:
        return 0

    table_fqn = table["fullyQualifiedName"]
    try:
        existing = open_task_keys(metadata, table_fqn)
    except Exception as err:
        logger.error(f"{table_fqn}: could not list existing tasks, skipping table: {err}")
        return 0

    reviewers = owner_names(table)
    done = 0
    for column_index, tag_index, column_name, proposal_fqn in candidates:
        real_fqn = f"{CLASSIFICATION}.{PROPOSAL_TAGS[proposal_fqn]}"
        key = (f"columns.{column_name}.tags", real_fqn)
        try:
            if key not in existing:
                file_owner_task(metadata, table, column_name, real_fqn, reviewers)
                existing.add(key)
                logger.info(f"{table_fqn}.{column_name}: filed owner task for {real_fqn}")
            removals.append((column_index, tag_index))
            done += 1
        except Exception as err:  # one bad column must not stop the run
            logger.error(f"{table_fqn}.{column_name}: could not file owner task for {real_fqn}: {err}")
    if removals:
        try:
            remove_tags(metadata, table, removals)
            logger.info(f"{table_fqn}: removed {len(removals)} proposal tag(s)")
        except Exception as err:
            logger.error(f"{table_fqn}: could not remove proposal tags (retried next run): {err}")
    return done


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    server_config = load_config_file(Path(sys.argv[1]))["workflowConfig"]["openMetadataServerConfig"]
    metadata = OpenMetadata(OpenMetadataConnection.model_validate(server_config))

    total = sum(process_table(metadata, table) for table in iter_tables(metadata))
    print(f"owner review: {total} proposal tag(s) handed over")


if __name__ == "__main__":
    main()
