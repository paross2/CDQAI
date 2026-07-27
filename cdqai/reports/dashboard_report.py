from __future__ import annotations

import html
import logging
from datetime import datetime

import pandas as pd

from cdqai.core.config import CDQAIConfig
from cdqai.data.dataset import CrashDataset
from cdqai.evidence.engine import EvidenceCollection
from cdqai.findings.finding import Finding


def _table(df: pd.DataFrame) -> str:
    if df.empty:
        return '<p class="empty">No records in this section.</p>'
    return df.to_html(index=False, border=0, classes="data", escape=True)


def _pct(value: float) -> str:
    return f"{float(value):g}"


def build_how_cdqai_works_html(config: CDQAIConfig) -> str:
    """Return the dashboard's technical explanation using active configuration values."""
    rules = config.raw.get("rules", {})
    sparse_length = int(rules.get("sparse_narrative", {}).get("minimum_length", 40))
    required = rules.get("required_fields", {}).get("rec01", [])
    required_text = ", ".join(str(x) for x in required) if required else "none configured"
    injury_cfg = rules.get("injury_conflict", {})
    injury_fields = injury_cfg.get("injury_field_candidates", [])
    injury_fields_text = ", ".join(str(x) for x in injury_fields)
    no_injury_values = injury_cfg.get("no_injury_values", [])
    no_injury_text = ", ".join(str(x) for x in no_injury_values)

    models = config.raw.get("models", {})
    structured = models.get("structured", {})
    narrative = models.get("narrative", {})
    ensemble = models.get("ensemble", {})
    model_evidence = config.raw.get("model_evidence", {})

    s_contamination = float(structured.get("contamination", 0.02)) * 100
    n_contamination = float(narrative.get("contamination", 0.02)) * 100
    max_numeric = int(structured.get("max_numeric_columns", 80))
    embedding_model = str(narrative.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2"))
    s_weight = float(ensemble.get("structured_weight", 0.5))
    n_weight = float(ensemble.get("narrative_weight", 0.5))
    s_threshold = float(model_evidence.get("structured_percentile", 99.0))
    n_threshold = float(model_evidence.get("narrative_percentile", 99.0))
    e_threshold = float(model_evidence.get("ensemble_percentile", 99.5))
    high_threshold = float(model_evidence.get("high_percentile", 99.75))
    critical_threshold = float(model_evidence.get("critical_percentile", 99.9))
    multi_min = int(model_evidence.get("multi_model_minimum", 2))

    return f'''
<section id="how-cdqai-works"><h2>How CDQAI Works</h2>
<p>CDQAI combines transparent data-quality rules with machine-learning anomaly detection. It does not declare that a crash record is wrong. It identifies observable evidence that may justify human review and organizes that evidence into a prioritized analyst queue.</p>

<h3>1. Load and validate the data</h3>
<p>CDQAI loads the configured crash-record and narrative tables from SQL Server, normalizes their crash identifiers into a common Master File Number (MFN), normalizes narrative text, validates required source fields, and merges the sources by MFN. The resulting analytical dataset is used by both the deterministic rules and the machine-learning models.</p>

<h3>2. Apply deterministic quality rules</h3>
<p>Deterministic rules are explicit checks. They do not depend on statistical similarity or learned patterns. Version {html.escape(config.version)} evaluates:</p>
<ul>
<li><strong>Missing narrative:</strong> the narrative is null, blank, or whitespace only.</li>
<li><strong>Sparse narrative:</strong> a nonblank narrative is shorter than the configured minimum of <strong>{sparse_length} characters</strong>. This is a review signal, not a conclusion that the narrative is incorrect.</li>
<li><strong>Missing required field:</strong> a configured required value is null or blank. Current REC01 required fields: <strong>{html.escape(required_text)}</strong>.</li>
<li><strong>Narrative injury conflict:</strong> injury-, EMS-, hospital-, fatality-, or death-related narrative language is compared with available coded injury fields. Candidate fields are <strong>{html.escape(injury_fields_text)}</strong>. Configured no-injury values include <strong>{html.escape(no_injury_text)}</strong>. The rule identifies a possible inconsistency; it does not determine which source is correct.</li>
</ul>
<p>Each rule-generated evidence item records the MFN, evidence category, severity, confidence, source rule, relevant fields, and supporting values.</p>

<h3>3. Score structured crash variables</h3>
<p>The structured model uses an <strong>Isolation Forest</strong> to evaluate unusual combinations of numeric coded crash variables. MFN is excluded, infinite values are converted to missing, missing numeric values are filled with zero, and variables are robustly scaled. Up to <strong>{max_numeric} numeric fields</strong> are used.</p>
<p>Isolation Forest repeatedly partitions the data. Records isolated in fewer partitions are considered more unusual. CDQAI negates the model decision function so larger values represent greater unusualness, then percentile-ranks the scores as <code>StructuredScore_pct</code>. A 99th-percentile record is more unusual than approximately 99% of records in that run.</p>
<p>The configured structured-model contamination is <strong>{_pct(s_contamination)}%</strong>. Contamination guides model fitting; it is not the final analyst-evidence threshold.</p>

<h3>4. Score crash narratives</h3>
<p>Each narrative is converted into a semantic embedding using <code>{html.escape(embedding_model)}</code>. Embeddings place narratives with similar overall meanings near one another even when they use different words. An Isolation Forest then identifies embeddings that are isolated from the broader narrative corpus.</p>
<p>A narrative may score highly because it describes a rare event, combines unusual concepts, uses atypical language or structure, or is otherwise distant from common narrative patterns. The model does not rely on a fixed suspicious-word list. Scores are percentile-ranked as <code>NarrativeScore_pct</code>. The configured narrative-model contamination is <strong>{_pct(n_contamination)}%</strong>.</p>

<h3>5. Convert model scores into evidence</h3>
<p>The structured and narrative percentiles are combined as:</p>
<p class="formula"><code>ModelEnsembleScore = ({_pct(s_weight)} × StructuredScore_pct) + ({_pct(n_weight)} × NarrativeScore_pct)</code></p>
<p>The ensemble results are ranked again to produce <code>ModelConfidence</code>. Model scores become formal evidence only at or above these configured thresholds:</p>
<table class="data"><thead><tr><th>Evidence or severity</th><th>Threshold</th><th>Interpretation</th></tr></thead><tbody>
<tr><td>Structured Anomaly</td><td>{_pct(s_threshold)}th percentile</td><td>Approximately the most unusual {100-s_threshold:g}% of structured records</td></tr>
<tr><td>Narrative Anomaly</td><td>{_pct(n_threshold)}th percentile</td><td>Approximately the most unusual {100-n_threshold:g}% of narratives</td></tr>
<tr><td>Ensemble Anomaly</td><td>{_pct(e_threshold)}th percentile</td><td>Approximately the most unusual {100-e_threshold:g}% after combining the models</td></tr>
<tr><td>High severity</td><td>{_pct(high_threshold)}th percentile</td><td>Approximately the most unusual {100-high_threshold:g}%</td></tr>
<tr><td>Critical severity</td><td>{_pct(critical_threshold)}th percentile</td><td>Approximately the most unusual {100-critical_threshold:g}%</td></tr>
</tbody></table>
<p>A <strong>Multi-Model Anomaly</strong> is generated when at least <strong>{multi_min}</strong> qualifying signals independently flag the same MFN. These signals may be structured, narrative, or ensemble evidence.</p>

<h3>6. Synthesize findings by MFN</h3>
<p>CDQAI groups all rule and model evidence by MFN. Version {html.escape(config.version)} uses a <strong>deterministic Finding Engine</strong>; it does not use Llama or another large language model. Records containing only missing- or sparse-narrative evidence remain completeness findings and are excluded from the actionable queue unless another signal exists.</p>
<p>The engine assigns a finding type, selects the highest-severity and highest-confidence primary issue, and calculates priority using:</p>
<p class="formula"><code>Priority score = 2 × highest severity + 2 × highest confidence + source-diversity adjustment + multi-source bonus</code></p>
<p>The source-diversity adjustment adds 0.75 for each additional distinct evidence source, up to three additions. A further 2-point bonus is added when two or more distinct sources agree. Scores map to Critical (13+), High (10–&lt;13), Medium (7–&lt;10), or Low (&lt;7).</p>
<p>Analyst explanations are assembled transparently from the messages attached to the evidence items. Duplicate messages are removed and the remainder are combined. No generative model creates new evidence or determines ground truth.</p>

<h3>7. Produce analyst and management reports</h3>
<p>CDQAI exports record-level evidence, synthesized findings, actionable and top-priority queues, annual findings summaries, model scores, run-level statistics, and this HTML dashboard. Annual summaries use the crash year associated with each MFN when a supported year field is available.</p>
<p><strong>Interpretation:</strong> the reports describe evidence observed during this run. Model percentiles measure relative unusualness within the analyzed dataset, not probability of error.</p></section>'''


def write_dashboard(dataset: CrashDataset, evidence: EvidenceCollection, findings: list[Finding], config: CDQAIConfig, logger: logging.Logger) -> None:
    outputs = config.raw.get("outputs", {})
    path = config.outputs_dir / outputs.get("dashboard_file", "dashboard.html")
    cats = pd.Series([x.category for x in evidence.items], dtype="object")
    actionable = [x for x in findings if x.actionable]
    metrics = {
        "Records Processed": dataset.metadata.merged_records,
        "Evidence Generated": len(evidence.items),
        "Actionable Findings": len(actionable),
        "High Priority": sum(x.priority_level == "High" for x in actionable),
        "Critical Priority": sum(x.priority_level == "Critical" for x in actionable),
        "Structured Anomalies": int((cats == "Structured Anomaly").sum()),
        "Narrative Anomalies": int((cats == "Narrative Anomaly").sum()),
        "Ensemble Anomalies": int((cats == "Ensemble Anomaly").sum()),
        "Multi-Model Anomalies": int((cats == "Multi-Model Anomaly").sum()),
        "Missing Narratives": int((cats == "Missing Narrative").sum()),
        "Sparse Narratives": int((cats == "Sparse Narrative").sum()),
    }
    pd.DataFrame([{"Metric": k, "Value": v, "Interpretation": "Observed evidence; not a conclusion of error"} for k, v in metrics.items()]).to_csv(
        config.outputs_dir / outputs.get("dashboard_summary_file", "dashboard_summary.csv"), index=False
    )
    cards = "".join(f'<div class="card"><strong>{v:,}</strong><span>{html.escape(k)}</span></div>' for k, v in metrics.items())
    top = pd.DataFrame([x.to_dict() for x in actionable[:50]])
    generated = datetime.now().strftime("%B %d, %Y %I:%M %p")
    explanation = build_how_cdqai_works_html(config)
    document = f'''<!doctype html><html><head><meta charset="utf-8"><title>CDQAI {config.version}</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f4f6f8;color:#17202a;line-height:1.5}}header{{background:#17365d;color:white;padding:32px 6%}}main{{max-width:1400px;margin:auto;padding:28px}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px}}.card,section{{background:white;border-radius:8px;padding:20px;box-shadow:0 1px 5px #ccd2d8}}.card strong{{display:block;font-size:30px}}.card span{{color:#4d5966}}section{{margin-top:22px}}section h3{{margin-top:28px;color:#17365d}}table.data{{border-collapse:collapse;width:100%;font-size:13px}}.data th,.data td{{border-bottom:1px solid #ddd;padding:8px;text-align:left;vertical-align:top}}.data th{{background:#e9eef4}}.note{{border-left:5px solid #17365d;padding:12px;background:#eef4fa}}.formula{{border-left:4px solid #66788a;background:#f6f8fa;padding:10px 12px}}footer{{padding:30px 6%;background:#17365d;color:white;margin-top:30px}}code{{background:#eef1f4;padding:2px 5px}}</style></head><body>
<header><h1>Crash Data Quality Artificial Intelligence (CDQAI)</h1><h2>Evidence and Review Dashboard — Version {html.escape(config.version)}</h2><p>CDQAI combines deterministic rules and machine-learning anomaly detection to prioritize Kentucky crash records for human review.</p></header>
<main><div class="note"><strong>Interpretation:</strong> CDQAI reports observable evidence and statistical unusualness. A finding is not a determination that a record is wrong. Analysts must review the underlying record and applicable business rules.</div>
<section><h2>About This Run</h2><div class="cards">{cards}</div></section>
{explanation}
<section><h2>Top Actionable Findings</h2>{_table(top)}</section>
<section><h2>Important Limitations</h2><p>Crash data alone cannot fully measure accessibility, timeliness, or integration across systems. Model percentiles describe relative unusualness within the analyzed dataset, not probability of error. Missing and sparse narratives are reported as completeness evidence and are excluded from the actionable queue unless another signal exists.</p></section></main>
<footer><strong>Crash Data Quality Artificial Intelligence (CDQAI)</strong><br>Version {html.escape(config.version)} · Kentucky Transportation Center · University of Kentucky<br>Generated: {generated}</footer></body></html>'''
    path.write_text(document, encoding="utf-8")
    logger.info("Dashboard written: %s", path)
