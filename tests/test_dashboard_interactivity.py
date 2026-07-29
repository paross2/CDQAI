import pandas as pd

from cdqai.reports.dashboard_report import _findings_table


def test_all_findings_table_includes_filters_and_unique_table_id():
    frame = pd.DataFrame([
        {
            "MFN": "123",
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
    assert 'class="filter-confidence-min"' in rendered
    assert 'all-findings-table-finding-detail-0' in rendered
