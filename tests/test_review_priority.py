# CDQAI file version: 2.3.6
from copy import deepcopy
from types import SimpleNamespace

import pandas as pd
import pytest

from cdqai.core.config import CDQAIConfig, DEFAULT_CONFIG
from cdqai.evidence.engine import EvidenceCollection
from cdqai.evidence.objects import Evidence
from cdqai.evidence.severity import Severity
from cdqai.findings.engine import FindingEngine
from cdqai.kentucky.quality import QualityCharacteristic
from cdqai.kentucky.records import RecordType
from cdqai.kentucky.systems import TrafficRecordSystem


def signal(category, source, severity=Severity.HIGH, confidence=0.95):
    return Evidence("FAKE", RecordType.REC01, TrafficRecordSystem.CRASH,
                    QualityCharacteristic.ACCURACY, category, severity, confidence,
                    "Fabricated evidence.", source)


def finding(tmp_path, code, items):
    raw = deepcopy(DEFAULT_CONFIG)
    raw["fields"] = {"normalized_mfn_field": "MFN", "narrative_text_field": "NarrativeTxt"}
    cfg = CDQAIConfig(raw, tmp_path)
    dataset = SimpleNamespace(merged=pd.DataFrame({"MFN": ["FAKE"], "KABCO": [code]}))
    return FindingEngine().run(EvidenceCollection(items=items), dataset, cfg)[0]


def test_missing_narrative_does_not_boost_minor_structured_finding(tmp_path):
    structured = signal("Structured Anomaly", "MODEL_STRUCTURED")
    missing = signal("Missing Narrative", "KY_REC01_MISSING_NARRATIVE", Severity.MEDIUM, 1.0)
    before = finding(tmp_path, "O", [structured])
    after = finding(tmp_path, "O", [structured, missing])
    assert after.priority_score == before.priority_score
    for key in ("ConfidenceScore", "Confidence", "EvidenceStrength", "EvidenceAgreement", "AnalystPriority"):
        assert after.to_dict()[key] == before.to_dict()[key]


def test_missing_narrative_bonus_depends_on_crash_severity(tmp_path):
    items = [signal("Structured Anomaly", "MODEL_STRUCTURED"),
             signal("Missing Narrative", "KY_REC01_MISSING_NARRATIVE", Severity.MEDIUM, 1.0)]
    ranked = [finding(tmp_path, code, items) for code in ["O", "C", "B", "A", "K"]]
    assert [x.completeness_bonus for x in ranked] == [0, 0.25, 0.25, 1, 1.5]
    assert ranked[0].priority_score < ranked[-1].priority_score
    unknown = finding(tmp_path, "not-mapped", items)
    assert unknown.crash_severity == "unknown"
    assert unknown.narrative_priority_weight == 1


def test_narrative_model_priority_is_lower_for_noninjury(tmp_path):
    items = [signal("Narrative Anomaly", "MODEL_NARRATIVE", Severity.CRITICAL, 1.0)]
    minor = finding(tmp_path, "O", items)
    severe = finding(tmp_path, "K", items)
    assert minor.priority_score < severe.priority_score
    assert minor.to_dict()["AnalystPriority"] == "Review as Resources Allow"
    assert severe.to_dict()["AnalystPriority"] == "Priority Review"


def test_derived_signals_do_not_raise_priority_or_strength(tmp_path):
    base = [signal("Structured Anomaly", "MODEL_STRUCTURED"), signal("Narrative Anomaly", "MODEL_NARRATIVE")]
    derived = [signal("Ensemble Anomaly", "MODEL_ENSEMBLE", Severity.CRITICAL, 1.0),
               signal("Multi-Model Anomaly", "MODEL_MULTI_SIGNAL", Severity.CRITICAL, 1.0)]
    before, after = finding(tmp_path, "K", base), finding(tmp_path, "K", base + derived)
    assert before.priority_score == after.priority_score
    assert before.to_dict()["ConfidenceScore"] == after.to_dict()["ConfidenceScore"]


@pytest.mark.parametrize("code", ["K", "A", "B", "C", "O", None])
def test_completeness_alone_stays_outside_actionable_queue(tmp_path, code):
    result = finding(tmp_path, code, [signal("Missing Narrative", "KY_REC01_MISSING_NARRATIVE")])
    assert not result.actionable
    assert result.priority_score <= 1.5
