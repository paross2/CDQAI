# CDQAI 2.0.2 User Guide

## Purpose

CDQAI prioritizes crash records for human review by combining deterministic evidence and machine-learning evidence. Findings are review leads, not declarations of error.

## Analytical Workflow

### Load and validate

Crash and narrative records are loaded from the configured SQL Server tables, MFNs are normalized, narrative text is normalized, and the sources are merged by MFN.

### Deterministic rules

The rule layer identifies observable conditions:

- missing narratives;
- narratives below the configured minimum length;
- null or blank configured required fields; and
- potential injury conflicts between narrative language and coded values.

The sparse-narrative default is 40 characters. The required fields, candidate injury fields, and no-injury values are configurable. Rule evidence describes a condition that warrants review; it does not determine correctness.

### Structured anomaly model

Numeric coded crash fields are cleaned, robustly scaled, and evaluated by an Isolation Forest. Records isolated in fewer model partitions receive higher anomaly values. CDQAI percentile-ranks those values as `StructuredScore_pct` so analysts can interpret each record relative to the analyzed dataset.

### Narrative anomaly model

Narratives are transformed into semantic embeddings using `sentence-transformers/all-MiniLM-L6-v2`. An Isolation Forest identifies embeddings that are isolated from the broader narrative corpus. This can reflect rare events, unusual concept combinations, atypical language or structure, or other semantic differences. The result is percentile-ranked as `NarrativeScore_pct`.

### Evidence thresholds

Default Version 2.0.2 thresholds are:

- Structured Anomaly: 99.0th percentile
- Narrative Anomaly: 99.0th percentile
- Ensemble Anomaly: 99.5th percentile
- High severity: 99.75th percentile
- Critical severity: 99.9th percentile
- Multi-Model Anomaly: at least two qualifying model signals

The dashboard displays values from the active configuration used for the run. Isolation Forest contamination defaults to 2% for both models, but contamination is a fitting assumption rather than the evidence-selection threshold.

### Finding synthesis

Evidence is grouped by MFN. The deterministic Finding Engine assigns a finding type, selects a primary issue, computes priority, and assembles the existing evidence messages into an explanation. Version 2.0.2 does not use Llama or another large language model.

Records supported only by missing- or sparse-narrative evidence remain completeness findings. They enter the actionable queue only when another signal exists for the same MFN.

## Priority Levels

The Finding Engine combines highest severity, highest confidence, source diversity, and independent multi-source agreement.

- **Critical:** priority score of 13 or higher.
- **High:** 10 to less than 13.
- **Medium:** 7 to less than 10.
- **Low:** less than 7.

A higher priority means stronger or more diverse evidence, not a greater proven probability that the record is wrong.

## Output Files

- `evidence.csv` contains one row per evidence signal.
- `findings.csv` groups all signals by MFN.
- `actionable_findings.csv` excludes records supported only by missing or sparse narratives.
- `top_findings.csv` is the ranked analyst queue.
- `annual_findings.csv` summarizes actionable findings by crash year when a supported year field is available.
- `dashboard_summary.csv` contains the metrics displayed on the dashboard.
- `dashboard.html` explains the active rules, models, thresholds, synthesis mechanism, and limitations.

## Review Workflow

1. Open `dashboard.html`.
2. Inspect the top actionable findings.
3. Locate the MFN in the appropriate source system.
4. Compare coded fields, narrative text, and supporting evidence.
5. Determine whether correction, clarification, or no action is appropriate.
6. Record the analyst disposition outside CDQAI.

A high model percentile means unusual relative to this run—not necessarily wrong.
