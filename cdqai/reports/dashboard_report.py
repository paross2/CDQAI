from __future__ import annotations

import html
import logging
from datetime import datetime

import pandas as pd

from cdqai.core.config import CDQAIConfig
from cdqai.core.build_info import (AI_ATTRIBUTION, CONTRIBUTING_DEVELOPER, CONTRIBUTOR_TITLE, DISCLAIMER, DOCUMENTATION_LICENSE, FUNDING_ACKNOWLEDGMENT, INSTITUTION, LEAD_DEVELOPER, LEAD_TITLE, ORGANIZATION, RELEASE_NAME, SOFTWARE_LICENSE, collect_build_info)
from cdqai.data.dataset import CrashDataset
from cdqai.evidence.engine import EvidenceCollection
from cdqai.findings.finding import Finding


def _table(df: pd.DataFrame) -> str:
    if df.empty:
        return '<p class="empty">No records in this section.</p>'
    return df.to_html(index=False, border=0, classes="data", escape=True)




def _findings_table(df: pd.DataFrame, table_id: str = "findings-table", include_filters: bool = False) -> str:
    if df.empty:
        return '<p class="empty">No records in this section.</p>'
    rows = []
    for index, row in df.iterrows():
        detail_id = f"{table_id}-finding-detail-{index}"
        priority = html.escape(str(row.get("PriorityLevel", "")))
        confidence = float(row.get("ConfidenceScore", 0) or 0)
        count = int(row.get("EvidenceCount", 0) or 0)
        issue = html.escape(str(row.get("PrimaryIssue", "")))
        strength = html.escape(str(row.get("EvidenceStrength", "")))
        analyst_priority = html.escape(str(row.get("AnalystPriority", "")))
        summary = (
            f'<tr class="finding-summary" data-primary-issue="{issue}" data-confidence="{confidence:.1f}" data-evidence-strength="{strength}" data-analyst-priority="{analyst_priority}"><td><button class="expand-button" type="button" aria-expanded="false" aria-controls="{detail_id}">+</button></td>'
            f'<td>{html.escape(str(row.get("MFN", "")))}</td><td>{issue}</td>'
            f'<td><span class="priority priority-{priority.lower()}">{priority}</span></td>'
            f'<td data-sort-value="{confidence:.1f}">{confidence:.1f}</td><td>{strength}</td>'
            f'<td data-sort-value="{count}">{count}</td><td>{analyst_priority}</td></tr>'
        )
        details = (
            f'<tr id="{detail_id}" class="finding-detail" hidden><td colspan="8"><div class="detail-grid">'
            f'<div><h4>Evidence agreement</h4><p>{html.escape(str(row.get("EvidenceAgreement", "")))}</p></div>'
            f'<div><h4>Recommended action</h4><p>{html.escape(str(row.get("RecommendedAction", "")))}</p></div>'
            f'<div><h4>Issue categories</h4><p>{html.escape(str(row.get("IssueCategories", "")))}</p></div>'
            f'<div><h4>Quality characteristics</h4><p>{html.escape(str(row.get("QualityCharacteristics", "")))}</p></div>'
            f'<div class="detail-wide"><h4>Explanation</h4><p>{html.escape(str(row.get("Explanation", "")))}</p></div>'
            f'<div class="detail-wide"><h4>Evidence sources</h4><p>{html.escape(str(row.get("RuleIDs", "")))}</p></div>'
            '</div></td></tr>'
        )
        rows.append(summary + details)
    issues = sorted({str(x) for x in df.get("PrimaryIssue", pd.Series(dtype="object")).dropna() if str(x)})
    strengths = sorted({str(x) for x in df.get("EvidenceStrength", pd.Series(dtype="object")).dropna() if str(x)})
    analyst_priorities = sorted({str(x) for x in df.get("AnalystPriority", pd.Series(dtype="object")).dropna() if str(x)})
    filters = ""
    if include_filters:
        issue_options = "".join(f'<option value="{html.escape(x)}">{html.escape(x)}</option>' for x in issues)
        strength_options = "".join(f'<option value="{html.escape(x)}">{html.escape(x)}</option>' for x in strengths)
        analyst_options = "".join(f'<option value="{html.escape(x)}">{html.escape(x)}</option>' for x in analyst_priorities)
        filters = f'''<div class="finding-filters" data-table="{table_id}">
<label>Search MFN or text<input type="search" class="filter-search" placeholder="Type to search"></label>
<label>Primary issue<select class="filter-issue"><option value="">All</option>{issue_options}</select></label>
<label>Evidence strength<select class="filter-strength"><option value="">All</option>{strength_options}</select></label>
<label>Analyst priority<select class="filter-analyst"><option value="">All</option>{analyst_options}</select></label>
<label>Minimum confidence<input type="number" class="filter-confidence-min" min="0" max="100" step="0.1" placeholder="0"></label>
<label>Maximum confidence<input type="number" class="filter-confidence-max" min="0" max="100" step="0.1" placeholder="100"></label>
<button type="button" class="clear-filters">Clear filters</button><span class="filter-count"></span></div>'''
    return filters + f'<div class="table-container"><table id="{table_id}" class="data findings-table sortable"><thead><tr><th></th><th>MFN</th><th>Primary Issue</th><th>Priority</th><th>Confidence</th><th>Evidence Strength</th><th>Signals</th><th>Analyst Priority</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>' 

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
<div id="how-cdqai-works">
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
<p><strong>Interpretation:</strong> the reports describe evidence observed during this run. Model percentiles measure relative unusualness within the analyzed dataset, not probability of error.</p></div>'''


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
    all_findings = pd.DataFrame([x.to_dict() for x in findings])
    generated = datetime.now().strftime("%B %d, %Y %I:%M %p")
    explanation = build_how_cdqai_works_html(config)
    build = collect_build_info(config.project_root)
    packages = "".join(f"<li><code>{html.escape(name)}</code> {html.escape(version)}</li>" for name, version in build["packages"].items())
    provenance = f'''<div id="about-cdqai"><div class="detail-grid"><div><h3>Project</h3><p><strong>{html.escape(config.project_name)} ({html.escape(config.short_name)})</strong><br>Version {html.escape(config.version)}<br>{html.escape(RELEASE_NAME)}</p></div><div><h3>Development</h3><p><strong>Lead Developer:</strong> {html.escape(LEAD_DEVELOPER)}, {html.escape(LEAD_TITLE)}<br><strong>Contributing Developer:</strong> {html.escape(CONTRIBUTING_DEVELOPER)}, {html.escape(CONTRIBUTOR_TITLE)}<br>{html.escape(ORGANIZATION)}<br>{html.escape(INSTITUTION)}</p></div><div><h3>Runtime</h3><p>Python {html.escape(str(build["python"]))}<br>{html.escape(str(build["operating_system"]))}<br>Git branch: {html.escape(str(build["git_branch"]))}<br>Git commit: {html.escape(str(build["git_commit"]))}<br>Git tag: {html.escape(str(build["git_tag"]))}</p></div><div><h3>Core Libraries</h3><ul>{packages}</ul></div><div class="detail-wide"><h3>AI-Assisted Development</h3><p>{html.escape(AI_ATTRIBUTION)}</p></div><div class="detail-wide"><h3>Funding</h3><p>{html.escape(FUNDING_ACKNOWLEDGMENT)}</p></div><div><h3>Licensing</h3><p>Software: {html.escape(SOFTWARE_LICENSE)}<br>Documentation: {html.escape(DOCUMENTATION_LICENSE)}</p></div><div class="detail-wide"><h3>Disclaimer</h3><p>{html.escape(DISCLAIMER)}</p></div></div></div>'''
    document = f'''<!doctype html><html><head><meta charset="utf-8"><title>CDQAI {config.version}</title>
<style>*{{box-sizing:border-box}}html,body{{max-width:100%;overflow-x:hidden}}body{{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f4f6f8;color:#17202a;line-height:1.5}}header{{background:#17365d;color:white;padding:clamp(24px,4vw,48px) 4vw}}main{{width:94%;max-width:1800px;margin:auto;padding:clamp(16px,2.5vw,36px) 0}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(220px,100%),1fr));gap:14px}}.card,section,.accordion{{min-width:0;background:white;border-radius:10px;padding:clamp(16px,2vw,24px);box-shadow:0 1px 5px #ccd2d8}}.card strong{{display:block;font-size:30px}}.card span{{color:#4d5966}}section{{margin-top:22px}}section h3{{margin-top:28px;color:#17365d}}.table-container{{width:100%;max-width:100%;overflow-x:auto;border:1px solid #d8dee5;border-radius:8px}}table.data{{border-collapse:collapse;width:100%;font-size:13px}}.data th,.data td{{border-bottom:1px solid #ddd;padding:9px;text-align:left;vertical-align:top;overflow-wrap:anywhere}}.data th{{background:#e9eef4;position:sticky;top:0;z-index:2;white-space:nowrap;cursor:pointer}}.findings-table{{min-width:980px}}.accordion{{min-width:0;background:white;border-radius:10px;box-shadow:0 1px 5px #ccd2d8}}.accordion>summary{{list-style:none;cursor:pointer;padding:clamp(16px,2vw,24px);font-size:1.5rem;font-weight:700;color:#17365d;display:flex;align-items:center;justify-content:space-between}}.accordion>summary::-webkit-details-marker{{display:none}}.accordion>summary::after{{content:"+";font-size:1.6rem}}.accordion[open]>summary::after{{content:"−"}}.accordion-content{{padding:0 clamp(16px,2vw,24px) clamp(16px,2vw,24px)}}.finding-filters{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;align-items:end;margin:0 0 14px;padding:14px;background:#f5f8fb;border:1px solid #d8dee5;border-radius:8px}}.finding-filters label{{display:flex;flex-direction:column;font-size:12px;font-weight:600;color:#34495e;gap:4px}}.finding-filters input,.finding-filters select{{width:100%;padding:8px;border:1px solid #aeb9c4;border-radius:5px;background:white}}.clear-filters{{padding:9px 14px;border:1px solid #7890aa;border-radius:5px;background:white;cursor:pointer}}.filter-count{{font-weight:600;color:#4d5966;align-self:center}}.expand-button{{width:28px;height:28px;border:1px solid #7890aa;background:white;border-radius:5px;font-size:18px;cursor:pointer}}.finding-detail td{{background:#f5f8fb;padding:16px}}.detail-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px 24px}}.detail-wide{{grid-column:1/-1}}.detail-grid h4{{margin:0 0 4px;color:#17365d}}.detail-grid p{{margin:0}}.priority{{display:inline-block;padding:3px 8px;border-radius:999px;font-weight:600}}.priority-critical{{background:#fde7e7;color:#8a1c1c}}.priority-high{{background:#fff0d9;color:#744600}}.priority-medium{{background:#e8f0fb;color:#244d7d}}.priority-low{{background:#edf1f4;color:#43515e}}.note{{border-left:5px solid #17365d;padding:12px;background:#eef4fa}}.formula{{border-left:4px solid #66788a;background:#f6f8fa;padding:10px 12px;overflow-wrap:anywhere}}footer{{padding:30px 4vw;background:#17365d;color:white;margin-top:30px}}code{{background:#eef1f4;padding:2px 5px}}@media(max-width:720px){{.detail-grid{{grid-template-columns:1fr}}.detail-wide{{grid-column:auto}}}}@media print{{.table-container{{overflow:visible}}.finding-detail[hidden]{{display:table-row}}}}</style></head><body>
<header><h1>Crash Data Quality Artificial Intelligence (CDQAI)</h1><h2>Evidence and Review Dashboard — Version {html.escape(config.version)}</h2><p>CDQAI combines deterministic rules and machine-learning anomaly detection to prioritize Kentucky crash records for human review.</p></header>
<main><div class="note"><strong>Interpretation:</strong> CDQAI reports observable evidence and statistical unusualness. A finding is not a determination that a record is wrong. Analysts must review the underlying record and applicable business rules.</div>
<section><h2>About This Run</h2><div class="cards">{cards}</div></section>
<details class="accordion"><summary>How CDQAI Works</summary><div class="accordion-content">{explanation}</div></details>
<details class="accordion"><summary>About CDQAI</summary><div class="accordion-content">{provenance}</div></details>
<details class="accordion" open><summary>Top Actionable Findings</summary><div class="accordion-content"><p>Expand a row for evidence agreement, recommended action, explanation, and sources. Click a column heading to sort.</p>{_findings_table(top, "top-findings-table")}</div></details>
<details class="accordion"><summary>All Findings</summary><div class="accordion-content"><p>Search and filter the complete findings set. Click any column heading to sort ascending or descending.</p>{_findings_table(all_findings, "all-findings-table", include_filters=True)}</div></details>
<section><h2>Important Limitations</h2><p>Crash data alone cannot fully measure accessibility, timeliness, or integration across systems. Model percentiles describe relative unusualness within the analyzed dataset, not probability of error. Missing and sparse narratives are reported as completeness evidence and are excluded from the actionable queue unless another signal exists.</p></section></main>
<footer><strong>Crash Data Quality Artificial Intelligence (CDQAI)</strong><br>Version {html.escape(config.version)} · Kentucky Transportation Center · University of Kentucky<br>Generated: {generated}</footer><script>
function findingGroups(table){{const groups=[];for(const row of [...table.tBodies[0].rows])if(row.classList.contains('finding-summary'))groups.push([row,row.nextElementSibling]);return groups;}}
for(const b of document.querySelectorAll('.expand-button')){{b.addEventListener('click',()=>{{const r=document.getElementById(b.getAttribute('aria-controls'));const opening=r.hidden;r.hidden=!opening;b.textContent=opening?'−':'+';b.setAttribute('aria-expanded',String(opening));}});}}
for(const table of document.querySelectorAll('table.sortable')){{[...table.querySelectorAll('thead th')].forEach((heading,index)=>{{if(!index)return;heading.addEventListener('click',()=>{{const groups=findingGroups(table);const ascending=heading.dataset.direction!=='asc';table.querySelectorAll('th').forEach(x=>delete x.dataset.direction);heading.dataset.direction=ascending?'asc':'desc';groups.sort((x,y)=>{{const A=x[0].cells[index],B=y[0].cells[index],av=A.dataset.sortValue??A.textContent.trim(),bv=B.dataset.sortValue??B.textContent.trim(),an=Number(av),bn=Number(bv);const comparison=!Number.isNaN(an)&&!Number.isNaN(bn)?an-bn:av.localeCompare(bv,undefined,{{numeric:true}});return ascending?comparison:-comparison;}});for(const group of groups)for(const row of group)table.tBodies[0].appendChild(row);}});}});}}
for(const controls of document.querySelectorAll('.finding-filters')){{const table=document.getElementById(controls.dataset.table);const search=controls.querySelector('.filter-search'),issue=controls.querySelector('.filter-issue'),strength=controls.querySelector('.filter-strength'),analyst=controls.querySelector('.filter-analyst'),minimum=controls.querySelector('.filter-confidence-min'),maximum=controls.querySelector('.filter-confidence-max'),count=controls.querySelector('.filter-count');const apply=()=>{{let visible=0;for(const [summary,detail] of findingGroups(table)){{const query=search.value.trim().toLowerCase(),confidence=Number(summary.dataset.confidence||0);const show=(!query||summary.textContent.toLowerCase().includes(query))&&(!issue.value||summary.dataset.primaryIssue===issue.value)&&(!strength.value||summary.dataset.evidenceStrength===strength.value)&&(!analyst.value||summary.dataset.analystPriority===analyst.value)&&(!minimum.value||confidence>=Number(minimum.value))&&(!maximum.value||confidence<=Number(maximum.value));summary.hidden=!show;if(detail)detail.hidden=true;const button=summary.querySelector('.expand-button');if(button){{button.textContent='+';button.setAttribute('aria-expanded','false');}}if(show)visible++;}}count.textContent=`${{visible.toLocaleString()}} finding${{visible===1?'':'s'}} shown`;}};for(const input of controls.querySelectorAll('input,select'))input.addEventListener('input',apply);controls.querySelector('.clear-filters').addEventListener('click',()=>{{for(const input of controls.querySelectorAll('input,select'))input.value='';apply();}});apply();}}
</script></body></html>'''
    path.write_text(document, encoding="utf-8")
    logger.info("Dashboard written: %s", path)
