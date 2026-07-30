# CDQAI — Crash Data Quality Artificial Intelligence

**Version 2.2.3 — Transparent Narrative Evidence**

CDQAI is a Kentucky-focused, AI-assisted crash-data review platform developed for the Kentucky Transportation Center. It combines transparent deterministic rules with structured and narrative anomaly models to identify records that warrant analyst review.

> CDQAI reports evidence, not conclusions. A finding indicates that a record is incomplete, internally inconsistent, or statistically unusual. It does not establish that the record is incorrect.

## How CDQAI Works

### 1. Load and validate

CDQAI loads the configured crash-record and narrative tables from SQL Server. Crash identifiers are normalized into a common Master File Number (MFN), narrative text is normalized, required source fields are validated, and the sources are merged by MFN. The merged dataset supports both deterministic rules and machine-learning models.

### 2. Apply deterministic rules

Deterministic rules are explicit, human-readable checks. They do not depend on statistical similarity or learned patterns.

- **Missing narrative:** the narrative is null, blank, or whitespace only.
- **Sparse narrative:** a nonblank narrative is shorter than the configured minimum. The default is 40 characters.
- **Missing required field:** a field listed under `rules.required_fields` is null or blank. The default example requires MFN.
- **Narrative injury conflict:** injury-, EMS-, hospital-, fatality-, or death-related language is compared with available coded injury fields. Evidence is created when the narrative contains an injury signal and a configured coded field contains a configured no-injury value.

A rule identifies an observable condition or possible inconsistency. It does not determine which value is correct.

### 3. Score structured crash variables

The structured model uses an Isolation Forest to evaluate unusual combinations of numeric coded crash variables. MFN is excluded; infinite values are converted to missing; missing numeric values are filled with zero; and fields are robustly scaled. The default configuration uses no more than 80 numeric fields.

Isolation Forest repeatedly partitions the data. Records isolated in fewer partitions are considered more unusual. CDQAI negates the model decision function so larger values represent greater unusualness, then converts scores to percentile ranks in `StructuredScore_pct`.

The default contamination value is 0.02, meaning the model is fitted while expecting an approximate 2% outlier fraction. Contamination guides model fitting; it is not the final evidence threshold.

### 4. Score crash narratives

Narratives are converted into semantic embeddings using `sentence-transformers/all-MiniLM-L6-v2`. The embeddings represent overall meaning, allowing narratives with similar concepts to be near one another even when they use different words.

An Isolation Forest evaluates these embeddings. A narrative can score highly because it describes a rare event, combines unusual concepts, uses atypical language or structure, or is otherwise distant from common narrative patterns. The model does not rely on a fixed suspicious-word list. Scores are percentile-ranked in `NarrativeScore_pct`.

### 5. Convert model scores into evidence

The default ensemble calculation is:

```text
ModelEnsembleScore =
    (0.5 × StructuredScore_pct)
    +
    (0.5 × NarrativeScore_pct)
```

The ensemble results are ranked again to produce `ModelConfidence`. Scores become formal evidence only after exceeding configured thresholds:

| Evidence or severity | Default threshold | Interpretation |
|---|---:|---|
| Structured Anomaly | 99.0th percentile | Approximately the most unusual 1% of structured records |
| Narrative Anomaly | 99.0th percentile | Approximately the most unusual 1% of narratives |
| Ensemble Anomaly | 99.5th percentile | Approximately the most unusual 0.5% after combining both models |
| High severity | 99.75th percentile | Approximately the most unusual 0.25% |
| Critical severity | 99.9th percentile | Approximately the most unusual 0.1% |

A Multi-Model Anomaly is generated when at least two qualifying structured, narrative, or ensemble signals flag the same MFN. Thresholds and weights are configurable in `config/config.yaml`. The dashboard reads and displays the active values used for the run.

### 6. Synthesize findings by MFN

CDQAI groups all rule and model evidence by MFN. Version 2.2.3 uses a deterministic Finding Engine; it does not use Llama or another large language model.

A finding containing only missing- or sparse-narrative evidence is treated as completeness information and excluded from the actionable queue unless another signal exists.

The Finding Engine:

1. assigns a finding type;
2. selects the highest-severity and highest-confidence primary issue;
3. calculates a priority score; and
4. combines the evidence messages into a transparent analyst explanation.

The priority formula is:

```text
Priority score =
    2 × highest severity
    + 2 × highest confidence
    + source-diversity adjustment
    + multi-source bonus
```

The source-diversity adjustment adds 0.75 for each additional distinct source, up to three additions. A 2-point bonus is added when at least two distinct sources agree.

| Priority | Score |
|---|---:|
| Critical | 13 or higher |
| High | 10 to less than 13 |
| Medium | 7 to less than 10 |
| Low | Less than 7 |

Explanations are assembled from existing evidence messages. Duplicate messages are removed. No generative model creates new evidence or determines ground truth.

### 7. Produce reports

CDQAI exports record-level evidence, synthesized findings, actionable and top-priority queues, annual findings summaries, model scores, run-level statistics, and an HTML dashboard. Annual summaries use the crash year associated with each MFN when a supported year field is available.

## Run Version 2.2.3 on Windows

Close any open output CSV files, then double-click:

```text
Run_CDQAI.bat
```

Or run:

```powershell
.\.venv\Scripts\python.exe run_cdqai.py --run-all
```


## Repository Layout

- `cdqai/` — application source code
- `config/` — local and example configuration
- `tests/` — automated tests
- `docs/` — architecture, methodology, and release documentation
- `outputs/`, `cache/`, and `logs/` — generated runtime artifacts kept outside the application package

`config/config.yaml` is intentionally ignored by Git because it may contain installation-specific database settings. Start from `config/config.example.yaml` when configuring a new installation.

## Primary Outputs

- `outputs/dashboard.html` — management and analyst dashboard
- `outputs/dashboard_summary.csv` — run-level evidence counts
- `outputs/evidence.csv` — all deterministic and model evidence
- `outputs/findings.csv` — all synthesized findings
- `outputs/actionable_findings.csv` — findings requiring substantive review
- `outputs/top_findings.csv` — highest-priority analyst queue
- `outputs/annual_findings.csv` — annual actionable-evidence trends
- `outputs/model_scores.csv` — record-level model scores

## Interpretation and Limitations

Model percentiles measure relative unusualness within the analyzed dataset; they are not probabilities of error. Crash data alone cannot fully measure accessibility, timeliness, or cross-system integration. Those characteristics require operational or external-system information beyond the crash record itself.

See `docs/USER_GUIDE.md`, `docs/TECHNICAL_ARCHITECTURE.md`, and `docs/RELEASE_NOTES_2.1.2.md` for additional detail.


## Authorship, Funding, and Licensing

CDQAI was conceived and led by **Paul Ross**, Research Scientist Principal, Kentucky Transportation Center, with contributions from **Nathaniel Swallom**, Research Scientist, Kentucky Transportation Center. Development was assisted by **OpenAI ChatGPT** as an engineering and documentation aid.

Development was supported through **Federal Traffic Safety Information Systems (Section 405(c))** grant funding administered by the **Kentucky Office of Highway Safety (KOHS)** under the **Kentucky Transportation Cabinet (KYTC)**.

Source code is licensed under the **MIT License**. Documentation is licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**. See `AUTHORS.md`, `LICENSE`, `LICENSE-DOCS`, and `CITATION.cff`.

## Context-Aware Analysis

Version 2.2.3 includes annual Kentucky county-level Mileage and Daily Vehicle Miles Traveled context for 1997–2025. CDQAI matches each crash to its exact context year when available, otherwise preferring the nearest prior year. County Number is retained for joining, filtering, and grouping but is excluded from global anomaly scoring by default.

Add the newest official KYTC workbook to `context/kentucky_dvmt/raw/` each year. CDQAI reports the context year used, fallback type, year gap, source file, and freshness status rather than failing when an exact year is unavailable. The generated `analysis_field_manifest.csv` identifies fields used, retained, or excluded.

## Dashboard narrative companion files (Version 2.2.3)

The dashboard now loads complete narratives on demand. Keep `dashboard.html` and `dashboard_narratives.js` together in the same output directory. When an analyst expands a finding with the `+` button, the dashboard reads that MFN's complete narrative from the companion JavaScript file and renders direct rule evidence with yellow highlighting. `finding_evidence.parquet` provides a durable analyst-ready copy of the full narrative and structured evidence spans; a CSV fallback is produced when Parquet support is unavailable.
