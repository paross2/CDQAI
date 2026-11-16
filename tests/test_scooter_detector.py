# CDQAI file version: 2.5.1
from copy import deepcopy

import pandas as pd
import pytest

from cdqai.core.config import CDQAIConfig, DEFAULT_CONFIG
from cdqai.data.dataset import CrashDataset
from cdqai.data.vehicle_types import _quoted_table
from cdqai.detectors.scooter import build_scooter_evidence
from cdqai.reports.review_selection import REVIEW_CONTROLS, REVIEW_SCRIPT


def _config(tmp_path):
    raw = deepcopy(DEFAULT_CONFIG)
    raw["fields"] = {
        "normalized_mfn_field": "MFN",
        "narrative_text_field": "NarrativeTxt",
    }
    raw["scooter_classifier"].update({
        "enabled": True,
        "training_file": str(tmp_path / "synthetic_training.csv"),
        "confidence_threshold": 0.55,
        "minimum_validation_precision": 0.0,
    })
    training = pd.DataFrame([
        {
            "Narrative": f"SYNTHETIC TEST: rider used a battery powered electric scooter on sample route {i}",
            "Scooter": "1",
        }
        for i in range(20)
    ] + [
        {
            "Narrative": f"SYNTHETIC TEST: driver operated a passenger sedan on sample route {i}",
            "Scooter": "0",
        }
        for i in range(20)
    ])
    training.to_csv(raw["scooter_classifier"]["training_file"], index=False)
    return CDQAIConfig(raw=raw, project_root=tmp_path)


def _dataset(vehicles):
    merged = pd.DataFrame([
        {"MFN": "201", "YR": 2024, "NarrativeTxt": "SYNTHETIC TEST: rider used a battery powered electric scooter."},
        {"MFN": "202", "YR": 2024, "NarrativeTxt": "SYNTHETIC TEST: rider used an electric scooter."},
    ])
    return CrashDataset(
        crashes=pd.DataFrame(),
        narratives=pd.DataFrame(),
        merged=merged,
        metadata=None,
        vehicle_type_records=vehicles,
    )


def test_scooter_candidates_skip_explicit_code_and_never_emit_narrative(tmp_path):
    config = _config(tmp_path)
    vehicles = pd.DataFrame([
        {"CDQAI_MFN": "201", "CDQAI_YEAR": 2024, "CDQAI_UNIT_TYPE": "12.0"},
        {"CDQAI_MFN": "202", "CDQAI_YEAR": 2024, "CDQAI_UNIT_TYPE": "01"},
    ])

    evidence, candidates, metadata = build_scooter_evidence(_dataset(vehicles), config)

    assert [item.mfn for item in evidence.items] == ["202"]
    assert "NarrativeTxt" not in evidence.items[0].supporting_values
    assert "SYNTHETIC TEST" not in evidence.items[0].message
    assert candidates.columns.tolist() == ["MFN", "ModelScore"]
    assert candidates["MFN"].tolist() == ["202"]
    assert metadata["candidate_count"] == 1
    assert evidence.items[0].supporting_values["score_is_calibrated_probability"] is False


def test_disabled_scooter_classifier_does_not_read_training_file(tmp_path):
    raw = deepcopy(DEFAULT_CONFIG)
    raw["scooter_classifier"]["training_file"] = str(tmp_path / "missing.csv")
    config = CDQAIConfig(raw=raw, project_root=tmp_path)

    evidence, candidates, metadata = build_scooter_evidence(
        _dataset(pd.DataFrame()), config
    )

    assert evidence.items == []
    assert candidates.empty
    assert metadata == {"enabled": 0, "candidate_count": 0}


def test_scooter_training_rejects_conflicting_labels_for_duplicate_text(tmp_path):
    config = _config(tmp_path)
    training_file = config.raw["scooter_classifier"]["training_file"]
    pd.DataFrame([
        {"Narrative": "SYNTHETIC TEST: identical sample narrative", "Scooter": label}
        for label in ["1", "0"] * 5
    ]).to_csv(training_file, index=False)
    vehicles = pd.DataFrame([
        {"CDQAI_MFN": "201", "CDQAI_YEAR": 2024, "CDQAI_UNIT_TYPE": "01"},
    ])

    with pytest.raises(ValueError, match="conflicting scooter labels"):
        build_scooter_evidence(_dataset(vehicles), config)


def test_vehicle_table_identifiers_reject_sql_fragments():
    with pytest.raises(ValueError, match="simple SQL identifier"):
        _quoted_table("ExternalCatalog.dbo.CrashDetails; DROP TABLE CrashDetails")


def test_scooter_mfn_only_pdf_control_is_removed():
    assert "print-scooter-mfns" not in REVIEW_SCRIPT
    assert "Potential uncoded e-scooter MFNs" not in REVIEW_CONTROLS
    assert "print-flagged" in REVIEW_CONTROLS
