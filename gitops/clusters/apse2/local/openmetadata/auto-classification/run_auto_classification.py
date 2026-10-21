"""Run the OpenMetadata auto-classification workflow and file its results as tag suggestions.

Usage: python run_auto_classification.py <workflow.yaml> <classification>...

Same as `metadata classify -c <workflow.yaml>`, with two differences:

* `metadata classify` (2.0.5) only scores tags of the PII classification:
  AutoClassificationWorkflow hardcodes classification_filter=[PII]. Here the classifications are
  given on the command line. Only classifications whose autoClassificationConfig.enabled is true
  are used.
* The sink would patch the scored tags straight onto the columns. Instead, each score is filed as
  a Suggestion task (POST /v1/tasks; the legacy POST /feed refuses tasks created by bots). The
  task follows SuggestionTaskWorkflow (suggestion-workflow.yaml): a Data Steward confirms within
  10 days, then the table owners approve. Nothing is written to the column until the Owner
  approves.

Task assignees and reviewers (the Steward step): the team named by $SUGGESTION_ASSIGNEE_TEAM, sent
as the team itself (not its members); if it is unset or does not exist, the workflow falls back to
the admins.
"""

import json
import os
import sys
import time
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

# Keep in sync with StewardConfirm.expiryTimer in suggestion-workflow.yaml.
STEWARD_REVIEW_DAYS = 10


def plain_reason(reason: Optional[str]) -> str:
    """The task UI shows `reasoning` as a plain <p> (no markdown, newlines collapse): strip the
    markdown the recognizers emit and keep it on one line."""
    text = " ".join((reason or "").replace("`", "").split())
    return text.replace(" - ", " ") or "auto-classification"


class TagSuggester:
    """Turns the column tags set by the classification processor into Suggestion tasks."""

    def __init__(self, metadata: OpenMetadata, reviewer_team: Optional[str], resuggest_rejected: bool = False):
        self.metadata = metadata
        self.reviewers = self._get_reviewers(reviewer_team)
        # Task statuses that do not block a new suggestion. Rejected only when testing.
        self.refile_statuses = {"Approved", "Expired"} | ({"Rejected"} if resuggest_rejected else set())
        if resuggest_rejected:
            logger.warning("SUGGESTION_RESUGGEST_REJECTED is on: rejected suggestions are filed again")

    def _get_reviewers(self, name: Optional[str]) -> list[str]:
        if not name:
            return []
        team = self.metadata.get_by_name(entity=Team, fqn=name)
        if team is None:
            logger.warning(f"Reviewer team {name!r} not found; the workflow assigns the admins")
            return []
        return [team.fullyQualifiedName.root]

    def _suggested(self, table_fqn: str) -> set[tuple[str, str]]:
        """(fieldPath, tagFQN) of every Suggestion task on the table that blocks a new one.

        Open and rejected tasks must not be filed again. Approved tasks do not block: while the tag
        is on the column the processor skips the column, so it only gets here once the tag was
        removed. Expired tasks (no Steward answer in time) do not block either, so the suggestion
        is filed again. With $SUGGESTION_RESUGGEST_REJECTED (testing), rejected ones do not block.
        """
        suggested, after = set(), None
        while True:
            params = {"type": "Suggestion", "aboutEntity": table_fqn, "fields": "payload", "limit": 100}
            if after:
                params["after"] = after
            page = self.metadata.client.get("/tasks", data=params) or {}
            for task in page.get("data", []):
                payload = task.get("payload") or {}
                if task.get("status") in self.refile_statuses or payload.get("suggestionType") != "Tag":
                    continue
                try:
                    labels = json.loads(payload.get("suggestedValue") or "[]")
                except ValueError:
                    continue
                suggested.update((payload.get("fieldPath"), label.get("tagFQN")) for label in labels)
            after = (page.get("paging") or {}).get("after")
            if not after:
                return suggested

    def suggest(self, record) -> None:
        table = record.entity
        if not isinstance(table, Table) or not record.column_tags:
            return
        table_fqn = table.fullyQualifiedName.root
        columns = {c.fullyQualifiedName.root: c for c in table.columns or []}
        try:
            suggested = self._suggested(table_fqn)
        except Exception as err:
            logger.error(f"{table_fqn}: could not list existing suggestions, skipping table: {err}")
            return

        for column_tag in record.column_tags:
            column = columns.get(column_tag.column_fqn)
            if column is None:
                continue
            label = column_tag.tag_label
            tag_fqn = label.tagFQN.root
            field_path = f"columns.{column.name.root}.tags"
            if (field_path, tag_fqn) in suggested:
                continue
            # What the task applies when approved: a confirmed tag, as Steward and Owner vouched for it.
            # The UI shows suggestedValue as raw JSON, so keep it to the tag and a one-line reason.
            suggestion = label.model_copy(
                update={
                    "state": State.Confirmed,
                    "labelType": LabelType.Generated,
                    "reason": plain_reason(label.reason),
                    "metadata": None,
                }
            )
            try:
                self.metadata.client.post(
                    "/tasks",
                    json={
                        "type": "Suggestion",
                        "category": "MetadataUpdate",
                        "displayName": f"{tag_fqn} cho {table.name.root}.{column.name.root}",
                        "about": f"<#E::table::{table_fqn}>",
                        # The workflow expands reviewer teams into their members when it computes
                        # assignees. A team sent as assignee is stored as is, so the task shows the
                        # team and any direct member can act on it.
                        # "assignees": self.reviewers,
                        # "reviewers": self.reviewers,
                        "dueDate": int((time.time() + STEWARD_REVIEW_DAYS * 86400) * 1000),
                        "payload": {
                            "suggestionType": "Tag",
                            "fieldPath": field_path,
                            "suggestedValue": json.dumps([suggestion.model_dump(mode="json", exclude_none=True)]),
                            "source": "AutoPilot",
                            "reasoning": (
                                f'Gợi ý thay đổi nhãn pháp lý: cột "{column.name.root}" thành nhãn "{tag_fqn}"'
                            ),
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
        suggester = TagSuggester(
            self.metadata,
            os.environ.get("SUGGESTION_ASSIGNEE_TEAM"),
            resuggest_rejected=os.environ.get("SUGGESTION_RESUGGEST_REJECTED", "").lower() in ("1", "true", "yes"),
        )
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
