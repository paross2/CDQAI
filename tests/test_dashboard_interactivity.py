# CDQAI file version: 2.5.1
import json
import logging

import pandas as pd

from cdqai.reports.dashboard_report import _findings_table, _write_paginated_findings_assets


def test_all_findings_table_includes_filters_and_unique_table_id():
    frame = pd.DataFrame([
        {
            "MFN": "123",
            "CrashYear": 2024,
            "PrimaryIssue": "Narrative Anomaly",
            "PriorityLevel": "High",
            "ConfidenceScore": 98.5,
            "EvidenceStrength": "Strong",
            "EvidenceCount": 3,
            "AnalystPriority": "Immediate Review",
            "EvidenceAgreement": "Multiple sources agree",
            "RecommendedAction": "Review narrative and coded fields",
            "IssueCategories": "Narrative Anomaly; Ensemble Anomaly",
            "QualityCharacteristics": "Accuracy",
            "Explanation": "Test explanation",
            "RuleIDs": "MODEL_NARRATIVE; MODEL_ENSEMBLE",
        }
    ])
    rendered = _findings_table(frame, "all-findings-table", include_filters=True)
    assert 'id="all-findings-table"' in rendered
    assert 'class="filter-issue"' in rendered
    assert 'class="filter-strength"' in rendered
    assert 'class="filter-narrative"' in rendered
    assert 'Has yellow highlights' in rendered
    assert 'class="flag-review"' in rendered
    assert 'data-categories="Narrative Anomaly; Ensemble Anomaly"' in rendered
    assert 'aria-label="Flag crash 123 for review"' in rendered
    assert 'class="filter-confidence-min"' in rendered
    assert 'all-findings-table-finding-detail-0' in rendered
    assert 'data-human-factors="[]"' in rendered
    assert 'data-factor-type="human"' in rendered
    assert 'data-factor-type="environmental"' in rendered
    assert 'data-factor-type="vehicle"' in rendered
    assert 'class="factor-filter-label factor-filter-human"' in rendered
    assert 'class="factor-filter-label factor-filter-environmental"' in rendered
    assert 'class="factor-filter-label factor-filter-vehicle"' in rendered
    assert 'background:#1d4ed8;border-color:#1d4ed8;color:white' in rendered
    assert 'background:#15803d;border-color:#15803d;color:white' in rendered
    assert 'background:#6b21a8;border-color:#6b21a8;color:white' in rendered
    assert "Tabular factor data not loaded." in rendered
    assert 'type="checkbox" class="factor-option" value="01"' not in rendered
    assert "Tabular coded factors" in rendered
    assert "These filters use only factor codes present in the configured tabular data" in rendered
    assert "Narrative-derived factors" in rendered
    assert "This section does not affect the current filters." in rendered
    assert 'class="factor-filter-title"' in rendered
    assert 'class="filter-search-row"' in rendered
    assert 'class="filter-options-grid"' in rendered
    assert 'class="factor-filter-row"' in rendered
    assert 'class="filter-footer"' in rendered
    assert 'grid-template-columns:repeat(3,minmax(0,1fr))' in rendered
    assert '@media(max-width:850px)' in rendered
    assert '@media(max-width:560px)' in rendered
    assert 'border:1px solid #d8dee5;border-radius:5px;background:white' in rendered
    assert 'border:1px solid #b42318;border-radius:5px;background:#b42318;color:white' in rendered
    assert 'max-height:300px;overflow:auto' in rendered
    assert 'Placeholder — narrative-derived factor detection is not implemented.' in rendered


def test_factor_codes_are_rendered_and_bound_to_crash_year():
    from cdqai.reports.dashboard_report import _factor_lookup

    frame = pd.DataFrame([{
        "MFN": "123",
        "CrashYear": 2024,
        "PrimaryIssue": "Narrative Anomaly",
        "PriorityLevel": "High",
        "ConfidenceScore": 98.5,
        "EvidenceStrength": "Strong",
        "EvidenceCount": 3,
    }])
    records = pd.DataFrame([
        {"FactorType": "human", "MFN": 123.0, "Year": 2024, "Code": 2},
        {"FactorType": "human", "MFN": 123, "Year": 2023, "Code": "04"},
        {"FactorType": "environmental", "MFN": 123, "Year": 2024, "Code": "99"},
    ])
    rendered = _findings_table(
        frame,
        "all-findings-table",
        include_filters=True,
        factor_lookup=_factor_lookup(records),
        factor_data_loaded=True,
    )
    assert 'data-human-factors="[&quot;02&quot;]"' in rendered
    assert "Cell Phone" in rendered
    assert "None Detected" in rendered
    assert 'type="checkbox" class="factor-option" value="02"' in rendered
    assert 'type="checkbox" class="factor-option" value="04"' in rendered
    assert 'type="checkbox" class="factor-option" value="01"' not in rendered
    assert 'width:18px;min-width:18px;height:18px;padding:0' in rendered
    assert 'disabled' not in rendered


def test_paginated_all_findings_keeps_details_out_of_initial_table(tmp_path):
    frame = pd.DataFrame([{
        "MFN": str(index),
        "CrashYear": 2024,
        "PrimaryIssue": "Narrative Anomaly",
        "PriorityLevel": "High",
        "ConfidenceScore": 98.5,
        "EvidenceStrength": "Strong",
        "EvidenceCount": 3,
        "AnalystPriority": "Immediate Review",
        "IssueCategories": "Narrative Anomaly",
        "EvidenceAgreement": "Narrative Model",
        "RecommendedAction": "Review narrative",
    } for index in range(101)])
    narratives = {
        str(index): {
            "narrativeFull": f"Synthetic narrative {index}",
            "evidenceSpans": [],
        }
        for index in range(101)
    }

    index_name = _write_paginated_findings_assets(
        frame, tmp_path, {}, False, narratives, logging.getLogger(__name__)
    )
    index_text = (tmp_path / index_name).read_text(encoding="utf-8")
    index = json.loads(index_text.removeprefix("window.CDQAIAllFindings = ").strip().removesuffix(";"))
    assert index["pageSize"] == 100
    assert len(index["records"]) == 101
    assert "Synthetic narrative" not in index_text
    chunks = sorted(tmp_path.glob("dashboard_finding_details_*.js"))
    assert len(chunks) == 1
    chunk_text = chunks[0].read_text(encoding="utf-8")
    chunk = json.loads(chunk_text.split("] = ", 1)[1].strip().removesuffix(";"))
    assert "Synthetic narrative 100" in chunk["narratives"]["100"]["narrativeFull"]
    assert "Narrative Model" in chunk["details"]["100"]

    rendered = _findings_table(frame, "all-findings-table", include_filters=True, paginated=True)
    assert 'class="pagination-controls"' in rendered
    assert 'data-paginated="true"' in rendered
    assert "Synthetic narrative 0" not in rendered
    assert "<tbody></tbody>" in rendered
