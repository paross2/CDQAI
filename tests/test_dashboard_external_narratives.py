import json
from types import SimpleNamespace

import pandas as pd

from cdqai.reports.dashboard_report import _findings_table, _narrative_payload


def test_full_narrative_is_not_embedded_in_findings_table():
    secret = "A complete narrative that should live only in the companion data file."
    frame = pd.DataFrame([{
        "MFN": "123", "PrimaryIssue": "Narrative anomaly", "PriorityLevel": "High",
        "ConfidenceScore": 99.1, "EvidenceCount": 1, "EvidenceStrength": "Strong",
        "AnalystPriority": "Immediate", "EvidenceAgreement": "One source",
        "RecommendedAction": "Review", "IssueCategories": "Narrative Anomaly",
        "QualityCharacteristics": "Accuracy", "Explanation": "Unusual narrative",
        "RuleIDs": "MODEL_NARRATIVE",
    }])
    rendered = _findings_table(frame)
    assert secret not in rendered
    assert 'class="narrative-slot"' in rendered
    assert 'data-mfn="123"' in rendered


def test_payload_keeps_complete_narrative_and_offsets():
    narrative = "Driver was AIRLIFTED after the collision. " + ("Additional detail. " * 50)
    payload = _narrative_payload(narrative, "airlifted")
    assert payload["narrativeFull"] == narrative
    assert len(payload["narrativePreview"]) == 500
    assert payload["evidenceSpans"][0]["text"] == "AIRLIFTED"
    assert narrative[payload["evidenceSpans"][0]["start"]:payload["evidenceSpans"][0]["end"]] == "AIRLIFTED"
    json.dumps(payload)


def test_embedding_only_payload_has_no_false_phrase_spans():
    payload = _narrative_payload("Unusual narrative content.", "")
    assert payload["evidenceSpans"] == []
    assert payload["evidenceMethod"] == "narrative_level_statistical"
