"""Run the OpenMetadata auto-classification workflow for the given classifications.

Usage: python run_auto_classification.py <workflow.yaml> <classification>...

Same as `metadata classify -c <workflow.yaml>`, except that `metadata classify` (2.0.5) only scores
tags of the PII classification: AutoClassificationWorkflow hardcodes classification_filter=[PII].
Only classifications whose autoClassificationConfig.enabled is true are used.
"""

import sys
from pathlib import Path

from metadata.cli.common import execute_workflow
from metadata.config.common import load_config_file
from metadata.pii.processor_factory import create_pii_processor
from metadata.workflow.classification import AutoClassificationWorkflow


class ScopedAutoClassificationWorkflow(AutoClassificationWorkflow):
    classifications: list[str] = []

    def _get_pii_processor(self):
        return create_pii_processor(
            self.metadata, self.config, classification_filter=self.classifications
        )


def main() -> None:
    config_path, *classifications = sys.argv[1:]
    if not classifications:
        sys.exit(__doc__)

    ScopedAutoClassificationWorkflow.classifications = classifications
    config = load_config_file(Path(config_path))
    workflow = ScopedAutoClassificationWorkflow.create(config)
    execute_workflow(workflow=workflow, config_dict=config)


if __name__ == "__main__":
    main()
