<!-- CDQAI file version: 2.5.0 -->
# CDQAI 2.5.0 User Guide

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

Approved numeric crash fields are evaluated by an Isolation Forest after median imputation. Identifiers, geography, county codes, raw HHMM time, and context fields are excluded by the field-role policy. There is no robust-scaling step. Records isolated in fewer model partitions receive higher anomaly values. CDQAI percentile-ranks those values as `StructuredScore_pct` so analysts can interpret each record relative to the analyzed dataset.

### Narrative anomaly model

Complete narratives are split into overlapping token-budgeted chunks. Their embeddings are pooled as a weighted mean plus an elementwise maximum, then scored together. Narrative and sentence-review coverage are shown separately in the dashboard. The first run after this upgrade rebuilds older truncated embedding caches.

Narratives are transformed into semantic embeddings using `sentence-transformers/all-MiniLM-L6-v2`. An Isolation Forest identifies embeddings that are isolated from the broader narrative corpus. This can reflect rare events, unusual concept combinations, atypical language or structure, or other semantic differences. The result is percentile-ranked as `NarrativeScore_pct`.

### Evidence thresholds

Default Version 2.5.0 thresholds are:

- Structured Anomaly: 99.0th percentile
- Narrative Anomaly: 99.0th percentile
- Ensemble Anomaly: 99.5th percentile
- High severity: 99.75th percentile
- Critical severity: 99.9th percentile
- Multi-Model Anomaly: at least two qualifying model signals

The dashboard displays values from the active configuration used for the run. Isolation Forest contamination defaults to 2% for both models and sets their decision threshold; it is not the evidence-selection threshold.

### Finding synthesis

Evidence is grouped by MFN. The deterministic Finding Engine assigns a finding type, selects a primary issue, computes priority, and assembles the existing evidence messages into an explanation. Version 2.5.0 does not use Llama or another large language model.

Records supported only by missing- or sparse-narrative evidence remain completeness findings. They enter the actionable queue only when another signal exists for the same MFN.

### Optional e-scooter narrative review

The local e-scooter classifier is disabled by default. When enabled, CDQAI trains
a TF-IDF/Logistic Regression classifier at run time from a labeled CSV stored
outside the repository, checks its precision on a stratified holdout, and
compares high-scoring narratives with a minimal projection of configured crash
identifier, year, and unit-type code. It emits review evidence only when the configured scooter
unit code is absent. The model score is not a calibrated probability or a
confirmed vehicle classification.

Before enabling it, configure the local `scooter_classifier` section in the
ignored `config/config.yaml`: set the private training-file path and local data
source identifiers and field names, and map `crash_year_field` to the matching
crash-source year field. The CSV defaults to `Narrative` and
`Scooter` columns with `1` as the positive class and `0` as the negative class;
column and label names can be configured. Keep all labeled crash records, connection details, and outputs out of GitHub.
The scooter code is configurable; verify it against the applicable codebook and
change the local setting if needed. The classifier
requires at least five distinct labeled narratives in each class, keeps
duplicate normalized narratives together during its holdout check, and rejects
models whose holdout precision is below the configured minimum.

Potential e-scooter findings remain in the findings tables and still require
human review. There is no separate MFN-only export control.

### Contributing-factor review

The dashboard can load the coded Human, Environmental, and Vehicle factor
records for a local review run. This feature is disabled by default. To enable
it, configure `factor_review` in the ignored local `config/config.yaml`:

- Set `enabled: true`.
- For each category, provide one or more local `database.schema.table` entries
  under `tables`.
- Confirm the MFN, year, and factor-code field names against the local schema.

Only MFN, year, and factor-code columns are projected from those tables. Use
generic placeholders in shared configuration; do not put local server names,
credentials, crash records, or training data in the repository.

In **All Findings**, tabular coded-factor filters include only codes present in
the configured factor tables; they do not inspect narrative text. Each category
filter supports multiple selected codes.
Selections within a category match any selected code; active filters across
categories are combined (all selected categories must match). Record details
show the coded factor codes and descriptions. Code 97 is **Other** and code 99
is **None Detected**.

**Narrative-derived factors** are shown in a separate placeholder section; no
narrative-derived factor detector is implemented, and those factors do not
affect the coded-factor filters. Factor data that was not loaded is identified
as unavailable, not interpreted as “None Detected.”

## Priority Levels

The Finding Engine combines substantive severity/confidence contributions and source-diversity bonuses. Derived ensemble summaries and narrative completeness do not inflate base-signal agreement. Narrative priority uses crash-severity weights; see ANALYST_GUIDANCE.md for the provisional policy.

- **Critical:** priority score of 13 or higher.
- **High:** 10 to less than 13.
- **Medium:** 7 to less than 10.
- **Low:** less than 7.

A higher priority means stronger or more diverse evidence, not a greater proven probability that the record is wrong.

## Output Files

The `Run_CDQAI.bat` launcher places each complete live run in a new folder
under `outputs` named `test_run_live_MM__DD_YYYY_H-MM` using local time. It
keeps that run's generated reports and log together and does not delete or
overwrite prior runs. If a folder for the same minute already exists, the
launcher stops rather than replacing it; start the next run after the clock
advances to a new minute.

Before a run, the launcher checks imports for packages declared in
`requirements.txt` and uses the selected Python interpreter's `pip` to install
only missing packages. Internet access may be required. If installation fails,
the launcher stops and displays the pip error rather than continuing with a
partial run.

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
3. Use the independent expand/collapse controls for each findings block.
4. In **All Findings**, optionally filter by one or more coded factors.
5. Locate the MFN in the appropriate source system.
6. Compare coded fields, narrative text, and supporting evidence.
7. Determine whether correction, clarification, or no action is appropriate.
8. Record the analyst disposition outside CDQAI.

A high model percentile means unusual relative to this run—not necessarily wrong.
