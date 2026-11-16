# CDQAI file version: 2.5.0
from __future__ import annotations

import html
import json
import logging
from datetime import datetime
import re
import hashlib

import pandas as pd

from cdqai.core.config import CDQAIConfig
from cdqai.core.build_info import (AI_ATTRIBUTION, REPOSITORY_URL, CONTRIBUTING_DEVELOPER, CONTRIBUTOR_TITLE, DISCLAIMER, DOCUMENTATION_LICENSE, FUNDING_ACKNOWLEDGMENT, INSTITUTION, LEAD_DEVELOPER, LEAD_TITLE, ORGANIZATION, RELEASE_NAME, SOFTWARE_LICENSE, collect_build_info)
from cdqai.data.dataset import CrashDataset
from cdqai.evidence.engine import EvidenceCollection
from cdqai.findings.finding import Finding
from cdqai.findings.severity_context import GROUPS, priority_settings
from cdqai.kentucky.factor_codes import FACTOR_CATALOGS, factor_description, normalize_factor_code
from cdqai.reports.review_selection import REVIEW_CONTROLS, REVIEW_SCRIPT
from cdqai.reports.finding_report import _year_map


def _table(df: pd.DataFrame) -> str:
    if df.empty:
        return '<p class="empty">No records in this section.</p>'
    return df.to_html(index=False, border=0, classes="data", escape=True)




def _canonical_mfn(value: object) -> str:
    """Normalize MFN values so integer, float, and string forms join reliably."""
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    if re.fullmatch(r"[+-]?\d+\.0+", text):
        text = text.split(".", 1)[0]
    return text


def _canonical_year(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    if re.fullmatch(r"\d+\.0+", text):
        text = text.split(".", 1)[0]
    return text


def _factor_lookup(records: pd.DataFrame | None) -> dict[tuple[str, str, str], list[str]]:
    lookup: dict[tuple[str, str, str], set[str]] = {}
    if records is None or records.empty:
        return {}
    for row in records.itertuples(index=False):
        factor_type = str(getattr(row, "FactorType", "")).strip().lower()
        if factor_type not in FACTOR_CATALOGS:
            continue
        key = (
            factor_type,
            _canonical_mfn(getattr(row, "MFN", "")),
            _canonical_year(getattr(row, "Year", "")),
        )
        code = normalize_factor_code(getattr(row, "Code", ""))
        if all(key) and code:
            lookup.setdefault(key, set()).add(code)
    return {key: sorted(codes) for key, codes in lookup.items()}


def _factor_detail_html(
    mfn: str,
    year: str,
    factor_lookup: dict[tuple[str, str, str], list[str]],
    factor_data_loaded: bool,
) -> str:
    if not factor_data_loaded:
        coded = '<p class="loading-note">Tabular coded factor data was not loaded. Configure and enable factor review to show these records.</p>'
    elif not year:
        coded = '<p class="loading-note">The crash year is unavailable, so factor rows cannot be matched safely.</p>'
    else:
        groups = []
        found = False
        for factor_type, catalog in FACTOR_CATALOGS.items():
            codes = factor_lookup.get((factor_type, mfn, year), [])
            found = found or bool(codes)
            items = "".join(
                f'<li><strong>{html.escape(code)}</strong> — '
                f'{html.escape(factor_description(factor_type, code))}</li>'
                for code in codes
            )
            content = f'<ul>{items}</ul>' if items else '<p>No linked factor codes were returned.</p>'
            groups.append(f'<h5>{html.escape(catalog["label"])}</h5>{content}')
        coded = "".join(groups)
        if not found:
            coded = '<p class="loading-note">No factor codes matched this MFN and crash year.</p>' + coded
    return (
        f'<div class="detail-wide coded-factors"><h4>Tabular coded factors</h4>{coded}</div>'
        '<div class="detail-wide narrative-derived-factors"><h4>Narrative-derived factors</h4>'
        '<p class="loading-note">Placeholder — narrative-derived factor detection is not implemented. '
        'This section is separate from the tabular coded-factor filters.</p></div>'
    )


def _factor_filter_html(factor_type: str, lookup: dict[tuple[str, str, str], list[str]], loaded: bool) -> str:
    catalog = FACTOR_CATALOGS[factor_type]
    disabled = "" if loaded else " disabled"
    codes = {
        code
        for (category, _, _), values in lookup.items()
        if category == factor_type
        for code in values
    }
    options = "".join(
        f'<label style="display:flex;flex-direction:row;align-items:flex-start;gap:8px;'
        f'padding:6px 4px;font-size:14px;font-weight:400;color:#17202a;cursor:pointer">'
        f'<input type="checkbox" class="factor-option" value="{html.escape(code)}"{disabled} '
        f'style="width:18px;min-width:18px;height:18px;padding:0;margin:2px 0 0;flex:0 0 18px">'
        f'<span style="flex:1;overflow-wrap:anywhere">{html.escape(code)} — '
        f'{html.escape(factor_description(factor_type, code))}</span></label>'
        for code in sorted(codes)
    )
    state = "" if loaded else ' aria-disabled="true"'
    load_note = "" if loaded else '<p class="loading-note">Tabular factor data not loaded. Configure and enable factor review.</p>'
    return (
        f'<details class="factor-filter" data-factor-type="{factor_type}" data-label="{html.escape(catalog["label"])}"{state}>'
        f'<summary>All {html.escape(catalog["label"])}</summary>'
        '<div class="factor-filter-menu" style="width:100%;min-width:100%;max-height:300px;overflow:auto;'
        'padding:8px;background:white;border:1px solid #aeb9c4;border-radius:5px">'
        '<div class="factor-filter-actions">'
        f'<button type="button" class="factor-select-all"{disabled}>Select all</button> '
        f'<button type="button" class="factor-clear"{disabled}>Clear</button></div>'
        f'{options}{load_note}'
        '</div></details>'
    )


def _build_narrative_lookup(dataset: CrashDataset, mfn_field: str, narrative_field: str) -> dict[str, str]:
    """Return the longest nonblank narrative for each canonical MFN."""
    lookup: dict[str, str] = {}
    frames = [dataset.merged, dataset.narratives]
    for frame in frames:
        if frame is None or frame.empty or mfn_field not in frame.columns or narrative_field not in frame.columns:
            continue
        for mfn_value, narrative_value in zip(frame[mfn_field], frame[narrative_field]):
            key = _canonical_mfn(mfn_value)
            narrative = "" if pd.isna(narrative_value) else str(narrative_value)
            if key and narrative.strip() and len(narrative) > len(lookup.get(key, "")):
                lookup[key] = narrative
    return lookup


def _analysis_summary(analysis, narrative):
    if not analysis or analysis.get("narrative_sha256") != hashlib.sha256(narrative.encode("utf-8")).hexdigest():
        return "Full-text model coverage unavailable for this displayed narrative."
    if analysis.get("status") != "complete":
        return "Full-text model analysis not completed for this narrative."
    review = analysis.get("review", {})
    status = review.get("status", "unavailable")
    if status in {"complete", "limited"}:
        explanation = f"Sentence review: {review.get('sentences_tested', 0)} of {review.get('sentences_total', 0)} sentences tested ({status})."
    else:
        explanation = {"disabled": "Sentence review disabled.", "not_selected": "Sentence review not selected under the review limit or score threshold.",
                       "input_score_mismatch": "Sentence review unavailable: re-encoded score did not match.",
                       "insufficient_sentences": "Sentence review unavailable: fewer than two sentences."}.get(status, "Sentence review unavailable.")
    return f"Full narrative processed: {analysis.get('tokens', 0)} tokens across {analysis.get('chunks', 0)} chunks. " + explanation


def _narrative_payload(text: object, terms: object = "", recorded_spans=None, narrative_model=True, analysis=None) -> dict[str, object]:
    """Create a portable, non-HTML narrative evidence payload."""
    narrative = "" if pd.isna(text) else str(text)
    term_list = sorted({x.strip() for x in str(terms or "").split(";") if x.strip()}, key=str.lower)
    spans: list[dict[str, object]] = []
    for term in sorted(term_list, key=len, reverse=True):
        for match in re.finditer(r"(?<!\w)" + re.escape(term) + r"(?!\w)", narrative, flags=re.I):
            spans.append({"start": match.start(), "end": match.end(), "text": match.group(0), "reason": "Direct phrase evidence from a deterministic rule"})
    spans.sort(key=lambda x: (int(x["start"]), -int(x["end"])))
    if recorded_spans is not None:
        spans = []
        digest = hashlib.sha256(narrative.encode("utf-8")).hexdigest()
        for span in recorded_spans:
            start, end = span.get("start"), span.get("end")
            if (isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(narrative)
                    and span.get("narrative_sha256") == digest and narrative[start:end] == span.get("text")):
                spans.append(dict(span))
        spans.sort(key=lambda x: (x["start"], -x["end"]))
    non_overlapping: list[dict[str, object]] = []
    cursor = -1
    for span in spans:
        if int(span["start"]) >= cursor:
            non_overlapping.append(span)
            cursor = int(span["end"])
    methods = {span.get("method", "direct_rule_phrase") for span in non_overlapping}
    method = ("mixed_rule_and_sensitivity" if len(methods) > 1 else next(iter(methods))) if methods else ("narrative_level_statistical" if narrative_model else "no_segment_evidence")
    explanation = ("Yellow highlights mark exact rule matches and/or sentences whose removal reduced the fitted narrative model score. Hover for the evidence method. Model sensitivity is not proof of error or causation."
                   if non_overlapping else "No supported segment highlight is available. Sentence review is bounded to selected high-scoring narratives; no individual passage is established as causal."
                   if narrative_model else "This finding has no recorded narrative-segment trigger. Review its structured or rule evidence.")
    if recorded_spans is None and not non_overlapping:
        explanation = "The narrative was statistically unusual as a whole. No individual word or sentence is presented as causal."
    if recorded_spans and not non_overlapping:
        explanation = "Recorded highlights do not match this complete narrative. Compare the source report and recorded evidence; no unsupported passages are highlighted."
    return {
        "narrativeFull": narrative,
        "narrativePreview": narrative[:500],
        "evidenceSpans": non_overlapping,
        "evidenceMethod": method,
        "analysisCoverage": _analysis_summary(analysis, narrative),
        "analysis": analysis or {},
        "evidenceExplanation": ("Yellow highlighting identifies language used by a deterministic rule." if method == "direct_rule_phrase" else explanation),
    }


def _highlight_narrative(text: object, terms: object) -> str:
    """Compatibility renderer used by tests and non-JavaScript consumers."""
    payload = _narrative_payload(text, terms)
    narrative = str(payload["narrativeFull"])
    if not narrative.strip():
        return '<p class="empty">No narrative is available for this record.</p>'
    pieces: list[str] = []
    cursor = 0
    for span in payload["evidenceSpans"]:
        start, end = int(span["start"]), int(span["end"])
        pieces.append(html.escape(narrative[cursor:start]))
        pieces.append(f'<mark>{html.escape(narrative[start:end])}</mark>')
        cursor = end
    pieces.append(html.escape(narrative[cursor:]))
    return f'<div class="narrative-evidence">{"".join(pieces)}</div><p class="attribution-note">{html.escape(str(payload["evidenceExplanation"]))}</p>'


def _review_guidance_html(row) -> str:
    facts = row.get("ReviewFacts", ())
    facts = facts if isinstance(facts, (list, tuple)) else ()
    items = "".join(f'<li><strong>{html.escape(str(fact["id"]))}</strong> '
                    f'{html.escape(str(fact["text"]))}<br><small>Fields: '
                    f'{html.escape(", ".join(fact["fields"]))}</small></li>' for fact in facts)
    breadcrumbs = f'<ol>{items}</ol>' if items else '<p>No additional field-level review context is available.</p>'
    draft = str(row.get("LLMGuidance", "") or "")
    status = html.escape(str(row.get("LLMStatus", "Disabled")))
    model = html.escape(str(row.get("LLMModel", "") or ""))
    guidance = (f'<p style="white-space:pre-wrap">{html.escape(draft)}</p>' if draft else
                '<p>Use the recorded evidence and deterministic recommendation above.</p>')
    return (f'<div class="detail-wide"><h4>Recorded triggers and fields worth checking</h4>{breadcrumbs}</div>'
            f'<div class="detail-wide"><h4>Why this priority?</h4><p>{html.escape(str(row.get("PriorityRationale", "")))}</p></div>'
            f'<div class="detail-wide"><h4>Local Llama review draft</h4><p>{status} {model}</p>{guidance}'
            '<p class="attribution-note">Optional analyst breadcrumbs, not new evidence. '
            'Verify statements against the cited evidence. A generated draft does not change the score or findings.</p></div>')


def _finding_details_cell(
    row,
    mfn: str,
    year: str,
    factor_lookup: dict[tuple[str, str, str], list[str]],
    factor_data_loaded: bool,
) -> str:
    return (
        '<td colspan="8"><div class="detail-grid">'
        f'<div><h4>Evidence agreement</h4><p>{html.escape(str(row.get("EvidenceAgreement", "")))}</p></div>'
        f'<div><h4>Recommended action</h4><p>{html.escape(str(row.get("RecommendedAction", "")))}</p></div>'
        f'<div><h4>Issue categories</h4><p>{html.escape(str(row.get("IssueCategories", "")))}</p></div>'
        f'<div><h4>Quality characteristics</h4><p>{html.escape(str(row.get("QualityCharacteristics", "")))}</p></div>'
        f'<div class="detail-wide"><h4>Explanation</h4><p>{html.escape(str(row.get("Explanation", "")))}</p></div>'
        f'{_review_guidance_html(row)}'
        f'<div class="detail-wide"><h4>Evidence sources</h4><p>{html.escape(str(row.get("RuleIDs", "")))}</p></div>'
        f'{_factor_detail_html(mfn, year, factor_lookup, factor_data_loaded)}'
        f'<div class="detail-wide"><h4>Narrative evidence</h4><div class="narrative-slot" data-mfn="{html.escape(mfn)}"><p class="loading-note">Open this record to load the complete narrative and highlighted evidence.</p></div></div>'
        '</div></td>'
    )


def _finding_index_record(row, factor_lookup, row_index: int) -> list:
    mfn = _canonical_mfn(row.get("MFN", ""))
    issue = str(row.get("PrimaryIssue", "") or "")
    priority = str(row.get("PriorityLevel", "") or "")
    confidence = float(row.get("ConfidenceScore", 0) or 0)
    strength = str(row.get("EvidenceStrength", "") or "")
    count = int(row.get("EvidenceCount", 0) or 0)
    analyst_priority = str(row.get("AnalystPriority", "") or "")
    narrative_status = str(row.get("NarrativeStatus", "unknown") or "unknown")
    year = _canonical_year(row.get("CrashYear", ""))
    factor_codes = [
        factor_lookup.get((factor_type, mfn, year), [])
        for factor_type in FACTOR_CATALOGS
    ]
    categories = str(row.get("IssueCategories", "") or "")
    search_text = " ".join(
        (mfn, issue, priority, f"{confidence:.1f}", strength, str(count), analyst_priority)
    ).lower()
    return [
        mfn, issue, priority, confidence, strength, count, analyst_priority,
        narrative_status, *factor_codes, categories, search_text, row_index,
    ]


def _write_paginated_findings_assets(
    df: pd.DataFrame,
    output_dir,
    factor_lookup,
    factor_data_loaded: bool,
    narrative_payload: dict[str, dict[str, object]],
    logger: logging.Logger,
) -> str:
    page_size = 100
    chunk_size = 500
    detail_prefix = "dashboard_finding_details_"
    records = []
    details = {}
    narratives = {}
    chunk_index = 0

    def write_chunk():
        nonlocal details, narratives, chunk_index
        if not details:
            return
        payload = {"details": details, "narratives": narratives}
        path = output_dir / f"{detail_prefix}{chunk_index:04d}.js"
        path.write_text(
            "window.CDQAIAllFindingDetails = window.CDQAIAllFindingDetails || {}; "
            f"window.CDQAIAllFindingDetails[{chunk_index}] = "
            + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            + ";\n",
            encoding="utf-8",
        )
        details = {}
        narratives = {}
        chunk_index += 1

    for row_index, (_, row) in enumerate(df.iterrows()):
        record = _finding_index_record(row, factor_lookup, row_index)
        records.append(record)
        mfn = record[0]
        year = _canonical_year(row.get("CrashYear", ""))
        detail_cell = _finding_details_cell(
            row, mfn, year, factor_lookup, factor_data_loaded
        )
        details[str(row_index)] = detail_cell
        if mfn in narrative_payload:
            narratives[mfn] = narrative_payload[mfn]
        if len(details) >= chunk_size:
            write_chunk()
    write_chunk()

    index_name = "dashboard_findings_index.js"
    index_path = output_dir / index_name
    index_path.write_text(
        "window.CDQAIAllFindings = "
        + json.dumps(
            {
                "pageSize": page_size,
                "detailChunkSize": chunk_size,
                "detailPrefix": detail_prefix,
                "records": records,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + ";\n",
        encoding="utf-8",
    )
    logger.info(
        "Wrote paginated dashboard index and %s on-demand detail chunks.",
        chunk_index,
    )
    return index_name


def _findings_table(
    df: pd.DataFrame,
    table_id: str = "findings-table",
    include_filters: bool = False,
    factor_lookup: dict[tuple[str, str, str], list[str]] | None = None,
    factor_data_loaded: bool = False,
    paginated: bool = False,
) -> str:
    if df.empty:
        return '<p class="empty">No records in this section.</p>'
    factor_lookup = factor_lookup or {}
    rows = []
    for index, row in (() if paginated else df.iterrows()):
        detail_id = f"{table_id}-finding-detail-{index}"
        mfn = _canonical_mfn(row.get("MFN", ""))
        year = _canonical_year(row.get("CrashYear", ""))
        factor_codes = {
            factor_type: factor_lookup.get((factor_type, mfn, year), [])
            for factor_type in FACTOR_CATALOGS
        }
        factor_attributes = " ".join(
            f'data-{factor_type}-factors="{html.escape(json.dumps(codes))}"'
            for factor_type, codes in factor_codes.items()
        )
        priority = html.escape(str(row.get("PriorityLevel", "")))
        confidence = float(row.get("ConfidenceScore", 0) or 0)
        count = int(row.get("EvidenceCount", 0) or 0)
        issue = html.escape(str(row.get("PrimaryIssue", "")))
        strength = html.escape(str(row.get("EvidenceStrength", "")))
        analyst_priority = html.escape(str(row.get("AnalystPriority", "")))
        narrative_status = html.escape(str(row.get("NarrativeStatus", "unknown")))
        categories = html.escape(str(row.get("IssueCategories", "")))
        raw_finding_index = row.get("FindingIndex")
        finding_index = (
            f' data-finding-index="{int(raw_finding_index)}"'
            if raw_finding_index is not None and not pd.isna(raw_finding_index)
            else ""
        )
        flag = (f'<label class="review-flag"><input type="checkbox" class="flag-review" '
                f'data-mfn="{html.escape(_canonical_mfn(mfn))}" aria-label="Flag crash {html.escape(mfn)} for review"> Flag for review</label>')
        summary = (f'<tr class="finding-summary" data-narrative-status="{narrative_status}" data-primary-issue="{issue}" data-categories="{categories}" data-confidence="{confidence:.1f}" data-evidence-strength="{strength}" data-analyst-priority="{analyst_priority}"{finding_index} {factor_attributes}><td><button class="expand-button" type="button" aria-expanded="false" aria-controls="{detail_id}" data-mfn="{html.escape(mfn)}"{finding_index}>+</button></td>'
                   f'<td>{html.escape(mfn)}</td><td>{issue}</td><td><span class="priority priority-{priority.lower()}">{priority}</span></td>'
                   f'<td data-sort-value="{confidence:.1f}">{confidence:.1f}</td><td>{strength}</td><td data-sort-value="{count}">{count}</td><td>{analyst_priority}</td></tr>')
        details = (
            f'<tr id="{detail_id}" class="finding-detail" hidden>'
            f'{_finding_details_cell(row, mfn, year, factor_lookup, factor_data_loaded)}</tr>'
        )
        summary = summary.replace('</button></td>', '</button>' + flag + '</td>', 1)
        rows.append(summary + details)
    issues = sorted({str(x) for x in df.get("PrimaryIssue", pd.Series(dtype="object")).dropna() if str(x)})
    strengths = sorted({str(x) for x in df.get("EvidenceStrength", pd.Series(dtype="object")).dropna() if str(x)})
    analyst_priorities = sorted({str(x) for x in df.get("AnalystPriority", pd.Series(dtype="object")).dropna() if str(x)})
    filters = ""
    if include_filters:
        issue_options = "".join(f'<option value="{html.escape(x)}">{html.escape(x)}</option>' for x in issues)
        strength_options = "".join(f'<option value="{html.escape(x)}">{html.escape(x)}</option>' for x in strengths)
        analyst_options = "".join(f'<option value="{html.escape(x)}">{html.escape(x)}</option>' for x in analyst_priorities)
        factor_filters = "".join(
            f'<div class="factor-filter-label factor-filter-{factor_type}">'
            f'<span class="factor-filter-title">'
            f'{html.escape(FACTOR_CATALOGS[factor_type]["label"])}</span>'
            f'{_factor_filter_html(factor_type, factor_lookup, factor_data_loaded)}</div>'
            for factor_type in FACTOR_CATALOGS
        )
        filters = f'''<style>
.finding-filters{{display:flex;flex-direction:column;align-items:stretch;gap:12px}}
.finding-filters .filter-search-row,.finding-filters .filter-footer{{display:flex;align-items:center;gap:12px;min-width:0}}
.finding-filters .filter-search-label{{width:100%;font-size:14px}}
.finding-filters .filter-options-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}
.finding-filters .filter-options-grid>label{{min-width:0}}
.finding-filters .factor-filter-row{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}
.finding-filters .factor-filter-label{{display:flex;flex-direction:column;gap:4px;min-width:0;padding:8px;border:1px solid #d8dee5;border-radius:5px;background:white}}
.finding-filters .factor-filter-title{{display:block;padding:6px 8px;border-radius:5px;font-size:12px;font-weight:700;color:#34495e}}
.finding-filters .factor-filter{{min-width:0}}
.finding-filters .factor-filter>summary{{display:block;min-width:0;padding:8px;border:1px solid #aeb9c4;border-radius:5px;background:white;cursor:pointer;overflow-wrap:anywhere}}
.finding-filters .factor-filter-human .factor-filter-title,.finding-filters .factor-filter-human .factor-filter>summary{{background:#1d4ed8;border-color:#1d4ed8;color:white}}
.finding-filters .factor-filter-environmental .factor-filter-title,.finding-filters .factor-filter-environmental .factor-filter>summary{{background:#15803d;border-color:#15803d;color:white}}
.finding-filters .factor-filter-vehicle .factor-filter-title,.finding-filters .factor-filter-vehicle .factor-filter>summary{{background:#6b21a8;border-color:#6b21a8;color:white}}
.finding-filters .factor-filter-section h4,.finding-filters .narrative-factor-placeholder h4{{margin:0;color:#17365d}}
.finding-filters .factor-filter-section>p,.finding-filters .narrative-factor-placeholder>p{{margin:2px 0 8px;font-size:12px;color:#596673}}
.finding-filters .narrative-factor-placeholder{{padding:10px;border:1px dashed #aeb9c4;border-radius:5px;background:#fff}}
.finding-filters .filter-footer{{justify-content:flex-start}}
.finding-filters .clear-filters{{flex:0 0 auto;padding:8px 12px;border:1px solid #b42318;border-radius:5px;background:#b42318;color:white;font:inherit;font-weight:600;cursor:pointer}}
.finding-filters .clear-filters:hover{{background:#912018;border-color:#912018}}
.finding-filters .clear-filters:focus-visible{{outline:3px solid #f3a6a0;outline-offset:2px}}
.finding-filters .filter-count{{min-width:0}}
@media(max-width:850px){{.finding-filters .filter-options-grid,.finding-filters .factor-filter-row{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
@media(max-width:560px){{.finding-filters .filter-options-grid,.finding-filters .factor-filter-row{{grid-template-columns:minmax(0,1fr)}}}}
</style>
<div class="finding-filters" data-table="{table_id}">
<div class="filter-search-row"><label class="filter-search-label">Search MFN or text<input type="search" class="filter-search" placeholder="Type to search"></label></div>
<div class="filter-options-grid">
<label>Primary issue<select class="filter-issue"><option value="">All</option>{issue_options}</select></label>
<label>Evidence strength<select class="filter-strength"><option value="">All</option>{strength_options}</select></label>
<label>Analyst priority<select class="filter-analyst"><option value="">All</option>{analyst_options}</select></label>
<label>Narrative review<select class="filter-narrative"><option value="">All</option><option value="highlighted">Has yellow highlights</option><option value="available">Text available, no highlights</option><option value="missing">Narrative unavailable</option></select></label>
<label>Minimum confidence<input type="number" class="filter-confidence-min" min="0" max="100" step="0.1" placeholder="0"></label>
<label>Maximum confidence<input type="number" class="filter-confidence-max" min="0" max="100" step="0.1" placeholder="100"></label>
</div>
<div class="factor-filter-section"><h4>Tabular coded factors</h4><p>These filters use only factor codes present in the configured tabular data; narrative text is not used.</p>
<div class="factor-filter-row">
{factor_filters}
</div>
</div>
<div class="narrative-factor-placeholder"><h4>Narrative-derived factors</h4><p>Placeholder — narrative-derived factor detection is not implemented. This section does not affect the current filters.</p></div>
<div class="filter-footer"><button type="button" class="clear-filters">Clear filters</button><span class="filter-count" aria-live="polite"></span></div></div>'''
    pagination = ""
    if paginated:
        pagination = f'''<div class="pagination-controls" data-table="{table_id}">
<label>Rows per page<select class="page-size"><option>50</option><option selected>100</option><option>250</option></select></label>
<button type="button" class="page-previous" disabled>Previous</button>
<span class="page-status" aria-live="polite">Loading findings…</span>
<button type="button" class="page-next" disabled>Next</button></div>'''
    paginated_attr = ' data-paginated="true"' if paginated else ""
    return filters + pagination + f'<div class="table-container"><table id="{table_id}" class="data findings-table sortable"{paginated_attr}><thead><tr><th></th><th>MFN</th><th>Primary Issue</th><th>Priority</th><th>Confidence</th><th>Evidence Strength</th><th>Signals</th><th>Analyst Priority</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'

def _pct(value: float) -> str:
    return f"{float(value):g}"


def build_how_cdqai_works_html(config: CDQAIConfig) -> str:
    """Return the dashboard's technical explanation using active configuration values."""
    rules = config.raw.get("rules", {})
    sparse_length = int(rules.get("sparse_narrative", {}).get("minimum_length", 40))
    required = rules.get("required_fields", {}).get("crash", [])
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
    embedding_model = str(narrative.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2"))
    s_weight = float(ensemble.get("structured_weight", 0.5))
    n_weight = float(ensemble.get("narrative_weight", 0.5))
    s_threshold = float(model_evidence.get("structured_percentile", 99.0))
    n_threshold = float(model_evidence.get("narrative_percentile", 99.0))
    e_threshold = float(model_evidence.get("ensemble_percentile", 99.5))
    high_threshold = float(model_evidence.get("high_percentile", 99.75))
    critical_threshold = float(model_evidence.get("critical_percentile", 99.9))
    multi_min = int(model_evidence.get("multi_model_minimum", 2))
    severity_field = str(config.raw.get("review_priority", {}).get("severity_field", "KABCO"))
    priority_rows = ""
    for group in GROUPS:
        bonus, weight = priority_settings(config, group)
        priority_rows += f'<tr><td>{html.escape(group.replace("_", " "))}</td><td>{weight:g}</td><td>+{bonus:g}</td></tr>'
    guidance_cfg = config.raw.get("analyst_guidance", {})
    guidance_state = "enabled" if guidance_cfg.get("enabled", False) else "disabled"

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
<li><strong>Missing required field:</strong> a configured required value is null or blank. Current crash-record required fields: <strong>{html.escape(required_text)}</strong>.</li>
<li><strong>Narrative injury conflict:</strong> injury-, EMS-, hospital-, fatality-, or death-related narrative language is compared with available coded injury fields. Candidate fields are <strong>{html.escape(injury_fields_text)}</strong>. Configured no-injury values include <strong>{html.escape(no_injury_text)}</strong>. The rule identifies a possible inconsistency; it does not determine which source is correct.</li>
</ul>
<p>Each rule-generated evidence item records the MFN, evidence category, severity, confidence, source rule, relevant fields, and supporting values.</p>

<h3>3. Score structured crash variables</h3>
<p>The structured model uses an <strong>Isolation Forest</strong> to evaluate unusual combinations of approved numeric crash variables. Identifiers, geography, county, raw HHMM time, and context fields are excluded. Infinite values become missing and numeric missing values use median imputation. There is no schema-order feature limit or robust-scaling step. Observed field-tail comparisons are review context, not causal feature attribution.</p>
<p>Isolation Forest repeatedly partitions the data. Records isolated in fewer partitions are considered more unusual. CDQAI negates the model decision function so larger values represent greater unusualness, then percentile-ranks the scores as <code>StructuredScore_pct</code>. A 99th-percentile record is more unusual than approximately 99% of records in that run.</p>
<p>The configured structured-model contamination is <strong>{_pct(s_contamination)}%</strong>. Contamination sets the model decision threshold; it is not the final analyst-evidence threshold.</p>

<h3>4. Score crash narratives</h3>
<p>Available narratives are represented with semantic embeddings using <code>{html.escape(embedding_model)}</code>. Every nonblank narrative is split into overlapping chunks within the model token budget. All chunks are encoded; a token-weighted mean and elementwise maximum form the full-text feature vector. Coverage is reported separately from bounded sentence-removal review. Blank narratives are excluded from narrative Isolation Forest fitting, scoring, and percentile ranking. Fewer than two available narratives produces no narrative score.</p>
<p>A narrative may score highly because it describes a rare event, combines unusual concepts, uses atypical language or structure, or is otherwise distant from common narrative patterns. The model does not rely on a fixed suspicious-word list. Scores are percentile-ranked as <code>NarrativeScore_pct</code>. The configured narrative-model contamination is <strong>{_pct(n_contamination)}%</strong>.</p>

<h3>5. Convert model scores into evidence</h3>
<p>The structured and narrative percentiles are combined as:</p>
<p class="formula"><code>ModelEnsembleScore = weighted sum of available scores / sum of available weights</code></p>
<p>Configured weights: structured {_pct(s_weight)}, narrative {_pct(n_weight)}. A missing narrative receives no semantic anomaly score; available weights are renormalized. Ensemble evidence requires both positively weighted model scores. A single model is not counted again as ensemble corroboration.</p>
<p>The ensemble results are ranked again to produce <code>ModelConfidence</code>. Model scores become formal evidence only at or above these configured thresholds:</p>
<table class="data"><thead><tr><th>Evidence or severity</th><th>Threshold</th><th>Interpretation</th></tr></thead><tbody>
<tr><td>Structured Anomaly</td><td>{_pct(s_threshold)}th percentile</td><td>Approximately the most unusual {100-s_threshold:g}% of structured records</td></tr>
<tr><td>Narrative Anomaly</td><td>{_pct(n_threshold)}th percentile</td><td>Approximately the most unusual {100-n_threshold:g}% of narratives</td></tr>
<tr><td>Ensemble Anomaly</td><td>{_pct(e_threshold)}th percentile</td><td>Approximately the most unusual {100-e_threshold:g}% after combining the models</td></tr>
<tr><td>High severity</td><td>{_pct(high_threshold)}th percentile</td><td>Approximately the most unusual {100-high_threshold:g}%</td></tr>
<tr><td>Critical severity</td><td>{_pct(critical_threshold)}th percentile</td><td>Approximately the most unusual {100-critical_threshold:g}%</td></tr>
</tbody></table>
<p>A <strong>Multi-Model Anomaly</strong> requires at least <strong>{multi_min}</strong> qualifying base model types (structured and narrative). Ensemble and multi-model summaries are derived from these base signals; they do not add independent corroboration.</p>

<h3>6. Synthesize findings by MFN</h3>
<p>CDQAI groups all rule and model evidence by MFN. Version {html.escape(config.version)} uses a <strong>deterministic Finding Engine</strong>; it does not use Llama or another large language model. Records containing only missing- or sparse-narrative evidence remain completeness findings and are excluded from the actionable queue unless another signal exists.</p>
<p>The engine keeps substantive evidence separate from narrative completeness. Derived model summaries do not add source-diversity bonuses when base evidence is present. Crash severity is read from the explicitly configured field <code>{html.escape(severity_field)}</code>; unrecognized or missing codes remain unknown.</p>
<p class="formula"><code>Priority = substantive evidence score + bounded narrative-completeness adjustment</code></p>
<p>The substantive score uses twice the maximum severity and twice the maximum confidence, with the narrative-model components scaled by the multiplier below. Source diversity adds 0.75 per additional substantive source (up to three) plus 2 for multiple substantive sources. Completeness adds no confidence or agreement bonus. Completeness-only findings have a zero substantive score and stay outside the actionable queue. Scores map to Critical (13+), High (10–&lt;13), Medium (7–&lt;10), or Low (&lt;7).</p>
<table class="data"><thead><tr><th>Crash severity group</th><th>Narrative priority multiplier</th><th>Missing/sparse narrative adjustment</th></tr></thead><tbody>{priority_rows}</tbody></table>
<p>These are configurable review-policy weights, not calibrated error probabilities. Raw anomaly percentiles are retained. Unknown crash severity is not treated as a minor crash.</p>
<p>Analyst explanations are assembled transparently from the messages attached to the evidence items. Duplicate messages are removed and the remainder are combined. No generative model creates new evidence or determines ground truth.</p>

<h3>7. Produce analyst and management reports</h3>
<p>Recorded triggers and fields worth checking accompany the deterministic explanation. Optional local Llama guidance is <strong>{guidance_state}</strong>. It drafts evidence-referenced review suggestions for a bounded number of top actionable findings after scoring. Drafts are separate, unverified analyst aids and cannot change scores, evidence, or rank. If local generation is unavailable, deterministic reports remain available.</p>
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
        "Findings with unknown crash severity": sum(f.crash_severity == "unknown" for f in findings),
    }
    pd.DataFrame([{"Metric": k, "Value": v, "Interpretation": "Observed evidence; not a conclusion of error"} for k, v in metrics.items()]).to_csv(
        config.outputs_dir / outputs.get("dashboard_summary_file", "dashboard_summary.csv"), index=False
    )
    cards = "".join(f'<div class="card"><strong>{v:,}</strong><span>{html.escape(k)}</span></div>' for k, v in metrics.items())
    top = pd.DataFrame([x.to_dict() for x in actionable[:50]])
    all_findings = pd.DataFrame([x.to_dict() for x in findings])
    year_frame = _year_map(dataset, config)
    mfn_field_for_year = config.raw["fields"]["normalized_mfn_field"]
    year_lookup = {
        _canonical_mfn(mfn): _canonical_year(year)
        for mfn, year in zip(year_frame[mfn_field_for_year], year_frame["CrashYear"])
    }
    for frame in (top, all_findings):
        if not frame.empty:
            frame["CrashYear"] = frame["MFN"].map(
                lambda value: year_lookup.get(_canonical_mfn(value), "")
            )
    factor_data_loaded = dataset.factor_records is not None
    factor_lookup = _factor_lookup(dataset.factor_records)
    mfn_field = config.raw["fields"]["normalized_mfn_field"]
    narrative_field = config.raw["fields"]["narrative_text_field"]
    narrative_lookup = _build_narrative_lookup(dataset, mfn_field, narrative_field)
    spans_by_mfn = {}
    analysis_by_mfn = {}
    model_mfns = set()
    for item in evidence.items:
        key = _canonical_mfn(item.mfn)
        spans_by_mfn.setdefault(key, []).extend(item.supporting_values.get("narrative_spans", []))
        if item.source == "MODEL_NARRATIVE":
            model_mfns.add(key)
            analysis_by_mfn.setdefault(key, []).append(item.supporting_values.get("narrative_analysis", {}))
    analysis_frame = getattr(dataset, "narrative_analysis", None)
    if analysis_frame is not None:
        for mfn, value in zip(analysis_frame[mfn_field], analysis_frame["NarrativeAnalysis"]):
            analysis_by_mfn.setdefault(_canonical_mfn(mfn), []).append(json.loads(value))
    def matching_analysis(mfn):
        digest = hashlib.sha256(narrative_lookup.get(mfn, "").encode("utf-8")).hexdigest()
        return next((a for a in analysis_by_mfn.get(mfn, []) if a.get("narrative_sha256") == digest), None)
    finding_mfns = {_canonical_mfn(x.mfn) for x in findings if _canonical_mfn(x.mfn)}
    narrative_payload = {
        mfn: _narrative_payload(narrative_lookup.get(mfn, ""),
            recorded_spans=spans_by_mfn.get(mfn, []), narrative_model=mfn in model_mfns, analysis=matching_analysis(mfn))
        for mfn in sorted(finding_mfns)
    }
    missing_flagged = [mfn for mfn, value in narrative_payload.items() if not str(value["narrativeFull"]).strip()]
    statuses = {mfn: ("missing" if not str(value["narrativeFull"]).strip() else
                     "highlighted" if value["evidenceSpans"] else "available")
                for mfn, value in narrative_payload.items()}
    for frame in (top, all_findings):
        if not frame.empty:
            frame["NarrativeStatus"] = frame["MFN"].map(lambda x: statuses.get(_canonical_mfn(x), "unknown"))
    finding_indices = {
        _canonical_mfn(row.get("MFN", "")): index
        for index, (_, row) in enumerate(all_findings.iterrows())
    }
    if not top.empty:
        top["FindingIndex"] = top["MFN"].map(
            lambda value: finding_indices.get(_canonical_mfn(value))
        )
    for status, label in (("highlighted", "Finding MFNs with yellow narrative highlights"),
                          ("available", "Finding MFNs with text but no highlights"),
                          ("missing", "Finding MFNs with no narrative text")):
        count = sum(value == status for value in statuses.values())
        cards += f'<div class="card"><strong>{count:,}</strong><span>{label}</span></div>'
    if missing_flagged:
        logger.warning("%s finding records have no narrative text available in the joined dataset; check source-year coverage and identifier matching locally.", len(missing_flagged))
    finding_index_name = _write_paginated_findings_assets(
        all_findings,
        config.outputs_dir,
        factor_lookup,
        factor_data_loaded,
        narrative_payload,
        logger,
    )

    evidence_rows = []
    for mfn, value in narrative_payload.items():
        evidence_rows.append({
            "MFN": mfn,
            "NarrativeFull": value["narrativeFull"],
            "NarrativePreview": value["narrativePreview"],
            "NarrativeEvidenceSpans": json.dumps(value["evidenceSpans"], ensure_ascii=False),
            "NarrativeEvidenceMethod": value["evidenceMethod"],
            "NarrativeEvidenceExplanation": value["evidenceExplanation"],
            "NarrativeAnalysisCoverage": value["analysisCoverage"],
            "NarrativeAnalysis": json.dumps(value["analysis"]),
        })
    evidence_frame = pd.DataFrame(evidence_rows)
    evidence_path = config.outputs_dir / outputs.get("finding_evidence_file", "finding_evidence.parquet")
    try:
        evidence_frame.to_parquet(evidence_path, index=False)
    except (ImportError, ModuleNotFoundError, ValueError) as exc:
        fallback = evidence_path.with_suffix(".csv")
        logger.warning("Could not write Parquet finding evidence (%s); writing %s instead.", exc, fallback)
        evidence_frame.to_csv(fallback, index=False)
    generated = datetime.now().strftime("%B %d, %Y %I:%M %p")
    explanation = build_how_cdqai_works_html(config)
    build = collect_build_info(config.project_root)
    packages = "".join(f"<li><code>{html.escape(name)}</code> {html.escape(version)}</li>" for name, version in build["packages"].items())
    random_seed = config.raw.get("models", {}).get("random_state", config.raw.get("random_seed", "not configured"))
    ai_models = (
        "<ul><li><strong>Structured anomaly detection:</strong> Isolation Forest</li>"
        "<li><strong>Narrative embeddings:</strong> sentence-transformers/all-MiniLM-L6-v2</li>"
        "<li><strong>Embedding ecosystem:</strong> Sentence Transformers and Hugging Face</li>"
        "<li><strong>Narrative anomaly detection:</strong> Isolation Forest over semantic embeddings</li>"
        "<li><strong>Finding engine:</strong> Deterministic</li>"
        f"<li><strong>Optional analyst guidance:</strong> {html.escape(str(config.raw.get('analyst_guidance', {}).get('model', '') or 'Disabled / not configured'))}; separate from scoring</li></ul>"
    )
    provenance = f'''<div id="about-cdqai"><div class="detail-grid">
<div><h3>Project</h3><p><strong>{html.escape(config.project_name)} ({html.escape(config.short_name)})</strong><br>Version {html.escape(config.version)}<br>{html.escape(RELEASE_NAME)}</p></div>
<div><h3>Development</h3><p><strong>Lead Developer:</strong> {html.escape(LEAD_DEVELOPER)}, {html.escape(LEAD_TITLE)}<br><strong>Contributing Developer:</strong> {html.escape(CONTRIBUTING_DEVELOPER)}, {html.escape(CONTRIBUTOR_TITLE)}<br>{html.escape(ORGANIZATION)}<br>{html.escape(INSTITUTION)}</p></div>
<div><h3>Runtime</h3><p><strong>Python:</strong> {html.escape(str(build["python"]))}<br><strong>Operating system:</strong> {html.escape(str(build["operating_system"]))}<br><strong>Architecture:</strong> {html.escape(str(build["architecture"]))}<br><strong>GPU:</strong> {html.escape(str(build["gpu"]))}</p></div>
<div><h3>Source Control</h3><p><strong>Repository:</strong> <a href="{html.escape(REPOSITORY_URL)}">{html.escape(REPOSITORY_URL)}</a><br><strong>Git branch:</strong> {html.escape(str(build["git_branch"]))}<br><strong>Git commit:</strong> {html.escape(str(build["git_commit"]))}<br><strong>Git tag:</strong> {html.escape(str(build["git_tag"]))}<br><strong>Working tree modified:</strong> {html.escape(str(build["git_dirty"]))}</p></div>
<div><h3>Core Libraries and AI Stack</h3><ul>{packages}</ul></div>
<div><h3>AI Models Used</h3>{ai_models}</div>
<div class="detail-wide"><h3>System Provenance</h3><p><strong>Run timestamp (UTC):</strong> {html.escape(str(build["generated_utc"]))}<br><strong>Random seed:</strong> {html.escape(str(random_seed))}<br><strong>CDQAI release:</strong> {html.escape(config.version)} — {html.escape(RELEASE_NAME)}</p></div>
<div class="detail-wide"><h3>AI-Assisted Development</h3><p>{html.escape(AI_ATTRIBUTION)}</p></div><div class="detail-wide"><h3>Funding</h3><p>{html.escape(FUNDING_ACKNOWLEDGMENT)}</p></div><div><h3>Licensing</h3><p>Software: {html.escape(SOFTWARE_LICENSE)}<br>Documentation: {html.escape(DOCUMENTATION_LICENSE)}</p></div><div class="detail-wide"><h3>Disclaimer</h3><p>{html.escape(DISCLAIMER)}</p></div></div></div>'''

    document = f'''<!doctype html><html><head><meta charset="utf-8"><title>CDQAI {config.version}</title>
<style>*{{box-sizing:border-box}}html,body{{max-width:100%;overflow-x:hidden}}body{{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f4f6f8;color:#17202a;line-height:1.5}}header{{background:#17365d;color:white;padding:clamp(24px,4vw,48px) 4vw}}main{{width:94%;max-width:1800px;margin:auto;padding:clamp(16px,2.5vw,36px) 0}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(220px,100%),1fr));gap:14px}}.card,section,.accordion{{min-width:0;background:white;border-radius:10px;padding:clamp(16px,2vw,24px);box-shadow:0 1px 5px #ccd2d8}}.card strong{{display:block;font-size:30px}}.card span{{color:#4d5966}}section{{margin-top:22px}}section h3{{margin-top:28px;color:#17365d}}.table-container{{width:100%;max-width:100%;overflow-x:auto;border:1px solid #d8dee5;border-radius:8px}}table.data{{border-collapse:collapse;width:100%;font-size:13px}}.data th,.data td{{border-bottom:1px solid #ddd;padding:9px;text-align:left;vertical-align:top;overflow-wrap:anywhere}}.data th{{background:#e9eef4;position:sticky;top:0;z-index:2;white-space:nowrap;cursor:pointer}}.findings-table{{min-width:980px}}.accordion{{min-width:0;background:white;border-radius:10px;box-shadow:0 1px 5px #ccd2d8}}.accordion>summary{{list-style:none;cursor:pointer;padding:clamp(16px,2vw,24px);font-size:1.5rem;font-weight:700;color:#17365d;display:flex;align-items:center;justify-content:space-between}}.accordion>summary::-webkit-details-marker{{display:none}}.accordion>summary::after{{content:"+";font-size:1.6rem}}.accordion[open]>summary::after{{content:"−"}}.accordion-content{{padding:0 clamp(16px,2vw,24px) clamp(16px,2vw,24px)}}.finding-filters{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;align-items:end;margin:0 0 14px;padding:14px;background:#f5f8fb;border:1px solid #d8dee5;border-radius:8px}}.finding-filters label{{display:flex;flex-direction:column;font-size:12px;font-weight:600;color:#34495e;gap:4px}}.finding-filters input,.finding-filters select{{width:100%;padding:8px;border:1px solid #aeb9c4;border-radius:5px;background:white}}.clear-filters{{padding:9px 14px;border:1px solid #7890aa;border-radius:5px;background:white;cursor:pointer}}.filter-count{{font-weight:600;color:#4d5966;align-self:center}}.pagination-controls{{display:flex;align-items:center;justify-content:flex-end;gap:10px;flex-wrap:wrap;margin:0 0 10px}}.pagination-controls .page-status{{font-weight:600;color:#4d5966}}.pagination-controls button,.pagination-controls select{{padding:8px 12px;border:1px solid #7890aa;border-radius:5px;background:white}}.pagination-controls label{{display:flex;align-items:center;gap:6px;font-size:13px;font-weight:600}}.pagination-controls button:disabled{{opacity:.55;cursor:not-allowed}}.expand-button{{width:28px;height:28px;border:1px solid #7890aa;background:white;border-radius:5px;font-size:18px;cursor:pointer}}.finding-detail td{{background:#f5f8fb;padding:16px}}.detail-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px 24px}}.detail-wide{{grid-column:1/-1}}.detail-grid h4{{margin:0 0 4px;color:#17365d}}.detail-grid p{{margin:0}}.priority{{display:inline-block;padding:3px 8px;border-radius:999px;font-weight:600}}.priority-critical{{background:#fde7e7;color:#8a1c1c}}.priority-high{{background:#fff0d9;color:#744600}}.priority-medium{{background:#e8f0fb;color:#244d7d}}.priority-low{{background:#edf1f4;color:#43515e}}.note{{border-left:5px solid #17365d;padding:12px;background:#eef4fa}}.formula{{border-left:4px solid #66788a;background:#f6f8fa;padding:10px 12px;overflow-wrap:anywhere}}.narrative-evidence{{position:relative;white-space:pre-wrap;background:#fff;border:1px solid #d8dee5;border-radius:7px;padding:14px;max-height:300px;overflow:auto}}mark{{background:#ffeb3b;color:#17202a;padding:1px 2px;border-radius:2px}}.attribution-note{{margin-top:8px!important;font-size:12px;color:#596673}}.evidence-label{{display:inline-block;margin-bottom:8px;padding:4px 8px;border-radius:999px;background:#e8f0fb;color:#244d7d;font-weight:700;font-size:12px}}.review-instruction{{margin-top:10px!important;padding:10px 12px;background:#eef4fa;border-left:4px solid #17365d}}.missing-narrative{{padding:12px;background:#fff3cd;border-left:4px solid #9a6700}}.loading-note{{color:#596673;font-style:italic}}footer{{padding:30px 4vw;background:#17365d;color:white;margin-top:30px}}code{{background:#eef1f4;padding:2px 5px}}@media(max-width:720px){{.detail-grid{{grid-template-columns:1fr}}.detail-wide{{grid-column:auto}}}}@media print{{.table-container{{overflow:visible}}.finding-detail[hidden]{{display:table-row}}}}</style></head><body>
<header><h1>Crash Data Quality Artificial Intelligence (CDQAI)</h1><h2>Evidence and Review Dashboard — Version {html.escape(config.version)}</h2><p>CDQAI combines deterministic rules and machine-learning anomaly detection to prioritize Kentucky crash records for human review.</p></header>
<main><div class="note"><strong>Interpretation:</strong> CDQAI reports observable evidence and statistical unusualness. A finding is not a determination that a record is wrong. Analysts must review the underlying record and applicable business rules.</div>
<section><h2>About This Run</h2><div class="cards">{cards}</div></section>
<details class="accordion"><summary>How CDQAI Works</summary><div class="accordion-content">{explanation}</div></details>
<details class="accordion"><summary>About CDQAI</summary><div class="accordion-content">{provenance}</div></details>
<details class="accordion" open><summary>Top Actionable Findings</summary><div class="accordion-content"><div class="block-expansion-controls" data-table="top-findings-table"><button type="button" class="clear-filters expand-block" data-open="true">Expand all</button> <button type="button" class="clear-filters expand-block" data-open="false">Collapse all</button><span> Applies only to this block.</span></div><p>Expand a row for evidence agreement, recommended action, explanation, and sources. Click a column heading to sort.</p>{_findings_table(top, "top-findings-table", factor_lookup=factor_lookup, factor_data_loaded=factor_data_loaded)}{REVIEW_CONTROLS}</div></details>
<details class="accordion"><summary>All Findings</summary><div class="accordion-content"><div class="block-expansion-controls" data-table="all-findings-table"><button type="button" class="clear-filters expand-block" data-open="true">Expand page</button> <button type="button" class="clear-filters expand-block" data-open="false">Collapse page</button><span> Applies only to the current page.</span></div><p>Search and filter the complete findings set. Navigate pages to review all matching records. Click a column heading to sort the complete result set.</p>{_findings_table(all_findings, "all-findings-table", include_filters=True, factor_lookup=factor_lookup, factor_data_loaded=factor_data_loaded, paginated=True)}</div></details>
<section><h2>Important Limitations</h2><p>Crash data alone cannot fully measure accessibility, timeliness, or integration across systems. Model percentiles describe relative unusualness within the analyzed dataset, not probability of error. Missing and sparse narratives are reported as completeness evidence and are excluded from the actionable queue unless another signal exists.</p></section></main>
<footer><strong>Crash Data Quality Artificial Intelligence (CDQAI)</strong><br>Version {html.escape(config.version)} · Kentucky Transportation Center · University of Kentucky<br>Generated: {generated}</footer><script src="{html.escape(str(finding_index_name))}"></script><script>
function findingGroups(table){{const groups=[],rows=table.tBodies[0].rows;for(let index=0;index<rows.length;index++){{const row=rows[index];if(row.classList.contains('finding-summary'))groups.push([row,row.nextElementSibling]);}}return groups;}}
function escapeHtml(value){{return String(value??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));}}
window.CDQAINarratives=window.CDQAINarratives||{{}};
const findingChunkPromises=new Map();
const loadedFindingChunks=[];
function rememberFindingChunk(chunk){{
 const previous=loadedFindingChunks.indexOf(chunk);
 if(previous>=0)loadedFindingChunks.splice(previous,1);
 loadedFindingChunks.push(chunk);
 while(loadedFindingChunks.length>2){{
  const expired=loadedFindingChunks.shift();
  for(const mfn of Object.keys(window.CDQAIAllFindingDetails[expired]?.narratives||{{}}))delete window.CDQAINarratives[mfn];
  delete window.CDQAIAllFindingDetails[expired];
  findingChunkPromises.delete(expired);
 }}
}}
function loadFindingChunk(index){{
 const metadata=window.CDQAIAllFindings;
 if(!metadata) return Promise.reject(new Error('The findings index is missing.'));
 const chunk=Math.floor(index/metadata.detailChunkSize),cached=window.CDQAIAllFindingDetails?.[chunk];
 if(cached){{rememberFindingChunk(chunk);return Promise.resolve(cached);}}
 if(findingChunkPromises.has(chunk))return findingChunkPromises.get(chunk);
 const filename=metadata.detailPrefix+String(chunk).padStart(4,'0')+'.js';
 const promise=new Promise((resolve,reject)=>{{
  const script=document.createElement('script');script.src=filename;
  script.onload=()=>{{const asset=window.CDQAIAllFindingDetails?.[chunk];if(asset){{rememberFindingChunk(chunk);resolve(asset);}}else reject(new Error(filename+' loaded without its detail data.'));}};
  script.onerror=()=>reject(new Error('Could not load '+filename+'. Keep the dashboard and its detail files together.'));
  document.head.appendChild(script);
 }});
 findingChunkPromises.set(chunk,promise);
 promise.catch(()=>findingChunkPromises.delete(chunk));
 return promise;
}}
function renderPagedFinding(index){{
 const record=window.CDQAIAllFindings.records[index],detailId='all-findings-table-finding-detail-'+index;
 const factors=record.slice(8,11).map(value=>escapeHtml(JSON.stringify(value)));
 return `<tr class="finding-summary" data-finding-index="${{index}}" data-narrative-status="${{escapeHtml(record[7])}}" data-primary-issue="${{escapeHtml(record[1])}}" data-categories="${{escapeHtml(record[11])}}" data-confidence="${{Number(record[3]).toFixed(1)}}" data-evidence-strength="${{escapeHtml(record[4])}}" data-analyst-priority="${{escapeHtml(record[6])}}" data-human-factors="${{factors[0]}}" data-environmental-factors="${{factors[1]}}" data-vehicle-factors="${{factors[2]}}"><td><button class="expand-button" type="button" aria-expanded="false" aria-controls="${{detailId}}" data-mfn="${{escapeHtml(record[0])}}" data-finding-index="${{index}}">+</button><label class="review-flag"><input type="checkbox" class="flag-review" data-mfn="${{escapeHtml(record[0])}}" aria-label="Flag crash ${{escapeHtml(record[0])}} for review"> Flag for review</label></td><td>${{escapeHtml(record[0])}}</td><td>${{escapeHtml(record[1])}}</td><td><span class="priority priority-${{escapeHtml(record[2].toLowerCase())}}">${{escapeHtml(record[2])}}</span></td><td data-sort-value="${{Number(record[3]).toFixed(1)}}">${{Number(record[3]).toFixed(1)}}</td><td>${{escapeHtml(record[4])}}</td><td data-sort-value="${{record[5]}}">${{record[5]}}</td><td>${{escapeHtml(record[6])}}</td></tr><tr id="${{detailId}}" class="finding-detail" data-paged="true" hidden><td colspan="8"><p class="loading-note">Expand to load finding details.</p></td></tr>`;
}}
function focusNarrativeEvidence(slot) {{
 const panel=slot.querySelector('.narrative-evidence'), mark=panel?.querySelector('mark');
 if(mark) panel.scrollTop=Math.max(0,mark.offsetTop-24);
}}
function renderNarrative(mfn,slot) {{
 if(!window.CDQAINarratives) {{slot.innerHTML='<p class="missing-narrative"><strong>Narrative companion unavailable.</strong> Keep dashboard_findings_index.js and its detail files from the same run together, then reload this page.</p>';return;}}
 const item=window.CDQAINarratives[mfn];
 if(!item||!String(item.narrativeFull||'').trim()) {{slot.innerHTML='<p class="missing-narrative"><strong>Narrative unavailable.</strong> Restore or rejoin the source narrative before spot-checking this record.</p>';return;}}
 const text=Array.from(String(item.narrativeFull)),spans=[...(item.evidenceSpans||[])].filter(s=>Number.isInteger(s.start)&&Number.isInteger(s.end)&&s.start>=0&&s.end>s.start&&s.end<=text.length&&text.slice(s.start,s.end).join('')===s.text).sort((a,b)=>a.start-b.start);
 let cursor=0,body='',count=0;
 for(const span of spans) {{if(span.start<cursor)continue;body+=escapeHtml(text.slice(cursor,span.start).join(''));body+='<mark title="'+escapeHtml(span.reason||'Highlighted evidence')+'">'+escapeHtml(text.slice(span.start,span.end).join(''))+'</mark>';cursor=span.end;count++;}}
 body+=escapeHtml(text.slice(cursor).join(''));
 const label=count?count+' yellow highlight'+(count===1?'':'s'):'No supported text highlight';
 const method=({{'direct_rule_phrase':'Rule-triggered language','sentence_removal_sensitivity':'Model sentence sensitivity','mixed_rule_and_sensitivity':'Rule and model sensitivity'}})[item.evidenceMethod]||'';
 const instruction=count?'Compare the highlighted passages with the coded fields and original report. Model sensitivity is a review aid, not proof of an error.':'Review the recorded triggers, coded fields, and complete narrative against the original report. No specific passage has been identified for highlighting in this finding.';
 slot.innerHTML='<div class="evidence-label">'+escapeHtml(label+(count&&method?' - '+method:''))+'</div><p class="analysis-coverage">'+escapeHtml(item.analysisCoverage||'Full-text model coverage unavailable for this displayed narrative.')+'</p><div class="narrative-evidence">'+body+'</div><p class="attribution-note">'+escapeHtml(item.evidenceExplanation||'')+'</p><p class="review-instruction"><strong>What to check:</strong> '+instruction+'</p>';
 focusNarrativeEvidence(slot);
}}
async function setFindingExpanded(button,opening) {{
 const row=document.getElementById(button.getAttribute('aria-controls'));
 row.hidden=!opening;button.textContent=opening?'-':'+';button.setAttribute('aria-expanded',String(opening));
 if(!opening)return;
 try {{
  const index=Number(button.dataset.findingIndex),asset=await loadFindingChunk(index),mfn=button.dataset.mfn;
  if(button.getAttribute('aria-expanded')!=='true')return;
  if(row.dataset.paged==='true')row.innerHTML=asset.details[index]||'<td colspan="8"><p class="missing-narrative">Finding details are missing from the companion file.</p></td>';
  if(asset.narratives[mfn])window.CDQAINarratives[mfn]=asset.narratives[mfn];
  const slot=row.querySelector('.narrative-slot');
  if(slot&&!slot.dataset.loaded){{renderNarrative(mfn,slot);slot.dataset.loaded='true';}}
  if(slot)focusNarrativeEvidence(slot);
 }} catch(error) {{
  if(row.dataset.paged==='true')row.innerHTML='<td colspan="8"><p class="missing-narrative">'+escapeHtml(error.message)+'</p></td>';
  else{{const slot=row.querySelector('.narrative-slot');if(slot)slot.innerHTML='<p class="missing-narrative">'+escapeHtml(error.message)+'</p>';}}
 }}
}}
document.addEventListener('click',event=>{{const button=event.target.closest('.expand-button');if(button)setFindingExpanded(button,button.getAttribute('aria-expanded')!=='true');}});
for(const controls of document.querySelectorAll('.block-expansion-controls')){{
 const table=document.getElementById(controls.dataset.table);if(!table)continue;
 for(const button of controls.querySelectorAll('.expand-block'))button.addEventListener('click',()=>{{
  const opening=button.dataset.open==='true',section=table.closest('details');
  if(opening&&section)section.open=true;
  for(const [summary] of findingGroups(table)){{if(opening&&summary.hidden)continue;const rowButton=summary.querySelector('.expand-button');if(rowButton)setFindingExpanded(rowButton,opening);}}
 }});
}}
for(const table of document.querySelectorAll('table.sortable')){{if(table.dataset.paginated==='true')continue;[...table.querySelectorAll('thead th')].forEach((heading,index)=>{{if(!index)return;heading.addEventListener('click',()=>{{const groups=findingGroups(table);const ascending=heading.dataset.direction!=='asc';table.querySelectorAll('th').forEach(x=>delete x.dataset.direction);heading.dataset.direction=ascending?'asc':'desc';groups.sort((x,y)=>{{const A=x[0].cells[index],B=y[0].cells[index],av=A.dataset.sortValue??A.textContent.trim(),bv=B.dataset.sortValue??B.textContent.trim(),an=Number(av),bn=Number(bv);const comparison=!Number.isNaN(an)&&!Number.isNaN(bn)?an-bn:av.localeCompare(bv,undefined,{{numeric:true}});return ascending?comparison:-comparison;}});for(const group of groups)for(const row of group)table.tBodies[0].appendChild(row);}});}});}}
for(const controls of document.querySelectorAll('.finding-filters')){{
 const table=document.getElementById(controls.dataset.table),pagination=document.querySelector(`.pagination-controls[data-table="${{controls.dataset.table}}"]`),metadata=window.CDQAIAllFindings;
 const search=controls.querySelector('.filter-search'),issue=controls.querySelector('.filter-issue'),strength=controls.querySelector('.filter-strength'),analyst=controls.querySelector('.filter-analyst'),narrative=controls.querySelector('.filter-narrative'),minimum=controls.querySelector('.filter-confidence-min'),maximum=controls.querySelector('.filter-confidence-max'),count=controls.querySelector('.filter-count'),factorFilters=[...controls.querySelectorAll('.factor-filter')];
 if(!metadata||!table||!pagination){{count.textContent='Findings index unavailable. Keep dashboard_findings_index.js beside this dashboard.';continue;}}
 const records=metadata.records,previous=pagination.querySelector('.page-previous'),next=pagination.querySelector('.page-next'),pageStatus=pagination.querySelector('.page-status'),pageSizeInput=pagination.querySelector('.page-size');
 let generation=0,searchTimer,pageSize=Number(pageSizeInput.value)||metadata.pageSize,page=1,filteredIndices=[],sortColumn=0,sortAscending=true;
 const renderPage=()=>{{
  const pageCount=Math.max(1,Math.ceil(filteredIndices.length/pageSize));page=Math.min(page,pageCount);
  const start=(page-1)*pageSize;table.tBodies[0].innerHTML=filteredIndices.slice(start,start+pageSize).map(renderPagedFinding).join('');
   if(window.CDQAIReviewSync)window.CDQAIReviewSync();
  pageStatus.textContent=`Page ${{page.toLocaleString()}} of ${{pageCount.toLocaleString()}} · ${{filteredIndices.length.toLocaleString()}} findings`;
  previous.disabled=page<=1;next.disabled=page>=pageCount;
 }};
 const sortResults=()=>{{
  if(sortColumn===0)return;
  const recordColumn=sortColumn-1;
  filteredIndices.sort((a,b)=>{{
   const av=records[a][recordColumn],bv=records[b][recordColumn],an=Number(av),bn=Number(bv);
   const comparison=av!==''&&bv!==''&&!Number.isNaN(an)&&!Number.isNaN(bn)?an-bn:String(av).localeCompare(String(bv),undefined,{{numeric:true}});
   return comparison===0?a-b:sortAscending?comparison:-comparison;
  }});
 }};
 const apply=()=>{{
  const current=++generation,query=search.value.trim().toLowerCase(),minValue=minimum.value?Number(minimum.value):null,maxValue=maximum.value?Number(maximum.value):null;
  const matches=[];
  const selectedFactors=Object.fromEntries(factorFilters.map(filter=>[filter.dataset.factorType,new Set([...filter.querySelectorAll('.factor-option:checked')].map(input=>input.value))]));
  const selectedCodes=Object.fromEntries(Object.entries(selectedFactors).map(([type,codes])=>[type,[...codes]]));
  for(const filter of factorFilters){{const selected=selectedFactors[filter.dataset.factorType],summary=filter.querySelector('summary');summary.textContent=selected.size?`${{selected.size}} selected`:`All ${{filter.dataset.label}}`;}}
  count.textContent='Filtering all findings…';
  const processBatch=start=>{{
   if(current!==generation)return;
   const end=Math.min(start+5000,records.length);
   for(let index=start;index<end;index++){{
    const record=records[index],factorsMatch=(!selectedCodes.human.length||selectedCodes.human.some(code=>record[8].includes(code)))&&(!selectedCodes.environmental.length||selectedCodes.environmental.some(code=>record[9].includes(code)))&&(!selectedCodes.vehicle.length||selectedCodes.vehicle.some(code=>record[10].includes(code)));
    if(factorsMatch&&(!query||record[12].includes(query))&&(!issue.value||record[1]===issue.value)&&(!strength.value||record[4]===strength.value)&&(!analyst.value||record[6]===analyst.value)&&(!narrative.value||record[7]===narrative.value)&&(minValue===null||record[3]>=minValue)&&(maxValue===null||record[3]<=maxValue))matches.push(index);
   }}
   if(end<records.length){{requestAnimationFrame(()=>processBatch(end));return;}}
   filteredIndices=matches;page=1;sortResults();renderPage();
   count.textContent=`${{matches.length.toLocaleString()}} finding${{matches.length===1?'':'s'}} match`;
  }};
  processBatch(0);
 }};
 const scheduleApply=event=>{{if(event.target===search){{clearTimeout(searchTimer);searchTimer=setTimeout(apply,150);}}else{{clearTimeout(searchTimer);apply();}}}};
 for(const input of controls.querySelectorAll('input,select'))input.addEventListener(input.type==='checkbox'?'change':'input',scheduleApply);
 for(const heading of table.querySelectorAll('thead th'))heading.addEventListener('click',()=>{{const column=[...table.querySelectorAll('thead th')].indexOf(heading);if(!column)return;sortAscending=sortColumn===column?!sortAscending:true;sortColumn=column;table.querySelectorAll('th').forEach(item=>delete item.dataset.direction);heading.dataset.direction=sortAscending?'asc':'desc';sortResults();page=1;renderPage();}});
 previous.addEventListener('click',()=>{{if(page>1){{page--;renderPage();}}}});
 next.addEventListener('click',()=>{{if(page<Math.ceil(filteredIndices.length/pageSize)){{page++;renderPage();}}}});
 pageSizeInput.addEventListener('change',()=>{{pageSize=Number(pageSizeInput.value)||metadata.pageSize;page=1;renderPage();}});
 for(const filter of factorFilters){{
  filter.querySelector('.factor-select-all').addEventListener('click',()=>{{for(const input of filter.querySelectorAll('.factor-option'))input.checked=true;apply();}});
  filter.querySelector('.factor-clear').addEventListener('click',()=>{{for(const input of filter.querySelectorAll('.factor-option'))input.checked=false;apply();}});
 }}
 controls.querySelector('.clear-filters').addEventListener('click',()=>{{clearTimeout(searchTimer);for(const input of controls.querySelectorAll('input,select')){{if(input.type==='checkbox')input.checked=false;else input.value='';}}apply();}});
 apply();
}}
{REVIEW_SCRIPT}
</script></body></html>'''
    path.write_text(document, encoding="utf-8")
    logger.info("Dashboard written: %s", path)
