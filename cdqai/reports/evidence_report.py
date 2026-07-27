from __future__ import annotations

import logging

from cdqai.core.config import CDQAIConfig
from cdqai.evidence.engine import EvidenceCollection


def write_evidence_outputs(
    evidence: EvidenceCollection,
    config: CDQAIConfig,
    logger: logging.Logger,
) -> None:
    outputs = config.raw.get("outputs", {})
    evidence_file = config.outputs_dir / outputs.get("evidence_file", "evidence.csv")
    summary_file = config.outputs_dir / outputs.get("evidence_summary_file", "evidence_summary.csv")

    logger.info("Writing evidence output: %s", evidence_file)
    evidence.to_dataframe().to_csv(evidence_file, index=False)

    logger.info("Writing evidence summary output: %s", summary_file)
    evidence.summary_dataframe().to_csv(summary_file, index=False)
