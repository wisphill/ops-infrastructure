"""Run the OpenMetadata auto-classification workflow and file its results as tag suggestions.

Usage: python run_auto_classification.py <workflow.yaml> <classification>...

Same as `metadata classify -c <workflow.yaml>`, with two differences:

* `metadata classify` (2.0.5) only scores tags of the PII classification:
  AutoClassificationWorkflow hardcodes classification_filter=[PII]. Here the classifications are
  given on the command line. Only classifications whose autoClassificationConfig.enabled is true
  are used.
* The sink would patch the scored tags straight onto the columns. Instead, each score is filed as
  a "Request Tag" task on the column, which a Data Steward reviews and accepts/rejects in the UI
  (Activity Feed > Tasks), see
  https://docs.open-metadata.org/v2.0.x/how-to-guides/data-collaboration/request-tags
  Nothing is written to the column until the task is accepted.

Task assignees: the team named by $SUGGESTION_ASSIGNEE_TEAM; if it is unset or does not exist, the
owners of the table.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

from metadata.cli.common import execute_workflow
from metadata.config.common import load_config_file
from metadata.generated.schema.entity.data.table import Table
from metadata.generated.schema.entity.teams.team import Team
from metadata.generated.schema.type.tagLabel import LabelType, State
from metadata.ingestion.ometa.ometa_api import OpenMetadata
from metadata.pii.processor_factory import create_pii_processor
from metadata.utils.logger import ingestion_logger
from metadata.workflow.classification import AutoClassificationWorkflow

logger = ingestion_logger()


class TagSuggester:
    """Turns the column tags set by the classification processor into Request Tag tasks."""

    def __init__(self, metadata: OpenMetadata, assignee_team: Optional[str]):
        self.metadata = metadata
        self.team = self._get_team(assignee_team)

    def _get_team(self, name: Optional[str]):
        if not name:
            return None
        team = self.metadata.get_by_name(entity=Team, fqn=name)
        if team is None:
            logger.warning(f"Assignee team {name!r} not found; falling back to table owners")
        return team

    def _assignees(self, table: Table) -> list[dict]:
        if self.team:
            return [{"id": str(self.team.id.root), "type": "team"}]
        owners = self.metadata.get_by_name(entity=Table, fqn=table.fullyQualifiedName.root, fields=["owners"])
        return [{"id": str(o.id.root), "type": o.type} for o in (owners.owners.root if owners and owners.owners else [])]

    def _already_suggested(self, entity_link: str, tag_fqn: str) -> bool:
        """True if a task (open, accepted or rejected) already exists for this column and tag.

        Accepted tasks leave the tag on the column, which the processor skips; rejected ones must
        not be re-suggested on the next run.
        """
        threads = self.metadata.client.get("/feed", data={"entityLink": entity_link, "type": "Task", "limit": 100})
        for thread in (threads or {}).get("data", []):
            details = thread.get("task") or {}
            if details.get("type") != "RequestTag":
                continue
            try:
                suggested = json.loads(details.get("suggestion") or "[]")
            except ValueError:
                continue
            if any(label.get("tagFQN") == tag_fqn for label in suggested):
                return True
        return False

    def suggest(self, record) -> None:
        table = record.entity
        if not isinstance(table, Table) or not record.column_tags:
            return
        table_fqn = table.fullyQualifiedName.root
        columns = {c.fullyQualifiedName.root: c for c in table.columns or []}
        assignees = self._assignees(table)
        if not assignees:
            logger.warning(f"{table_fqn}: no assignee team or owner; tasks are created unassigned")

        for column_tag in record.column_tags:
            column = columns.get(column_tag.column_fqn)
            if column is None:
                continue
            label = column_tag.tag_label
            tag_fqn = label.tagFQN.root
            entity_link = f"<#E::table::{table_fqn}::columns::{column.name.root}>"
            try:
                if self._already_suggested(entity_link, tag_fqn):
                    continue
                # What the task applies when accepted: a confirmed tag, as a Steward vouched for it.
                suggestion = label.model_copy(update={"state": State.Confirmed, "labelType": LabelType.Generated})
                self.metadata.client.post(
                    "/feed",
                    json={
                        "message": f"Suggested tag {tag_fqn} for {column.name.root}: {label.reason or 'auto-classification'}",
                        "about": entity_link,
                        "type": "Task",
                        "taskDetails": {
                            "type": "RequestTag",
                            "suggestion": json.dumps([suggestion.model_dump(mode="json", exclude_none=True)]),
                            "assignees": assignees,
                        },
                    },
                )
                logger.info(f"Suggested {tag_fqn} for {column_tag.column_fqn}")
            except Exception as err:  # one bad column must not stop the run
                logger.error(f"Could not suggest {tag_fqn} for {column_tag.column_fqn}: {err}")


class SuggestingAutoClassificationWorkflow(AutoClassificationWorkflow):
    classifications: list[str] = []

    def _get_pii_processor(self):
        processor = create_pii_processor(
            self.metadata, self.config, classification_filter=self.classifications
        )
        suggester = TagSuggester(self.metadata, os.environ.get("SUGGESTION_ASSIGNEE_TEAM"))
        scored = processor._run

        def run_and_suggest(record):
            result = scored(record)
            suggester.suggest(record)
            # The sink patches record.column_tags onto the columns: leave it nothing to apply.
            record.column_tags = []
            return result

        processor._run = run_and_suggest
        return processor


def main() -> None:
    config_path, *classifications = sys.argv[1:]
    if not classifications:
        sys.exit(__doc__)

    SuggestingAutoClassificationWorkflow.classifications = classifications
    config = load_config_file(Path(config_path))
    workflow = SuggestingAutoClassificationWorkflow.create(config)
    execute_workflow(workflow=workflow, config_dict=config)


if __name__ == "__main__":
    main()
