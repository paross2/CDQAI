# CDQAI 2.0 Technical Architecture

`run_cdqai.py` delegates to `cdqai.main`. The `--run-all` workflow loads a `CrashDataset`, runs `RuleEngine`, runs structured and narrative model scoring, converts extreme scores through `cdqai.evidence.model_evidence`, combines evidence in `EvidenceCollection`, synthesizes MFN-level findings through `FindingEngine`, and writes reports and the dashboard.

The Evidence object is the integration contract. Rules and models produce evidence; findings and reports consume evidence. This preserves deterministic traceability while allowing additional detectors to be added without rewriting downstream reporting.

Model thresholds are configured under `model_evidence`. Defaults are 99th percentile for structured and narrative evidence, 99.5th percentile for ensemble evidence, 99.75th percentile for High severity, and 99.9th percentile for Critical severity.
