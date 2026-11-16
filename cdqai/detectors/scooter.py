# CDQAI file version: 2.5.1
"""Opt-in local classifier for narrative-indicated scooters absent from unit coding."""
from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score
from sklearn.model_selection import StratifiedGroupKFold

from cdqai.core.config import CDQAIConfig
from cdqai.data.dataset import CrashDataset
from cdqai.evidence.engine import EvidenceCollection
from cdqai.evidence.objects import Evidence
from cdqai.evidence.severity import Severity
from cdqai.kentucky.quality import QualityCharacteristic
from cdqai.kentucky.records import RecordType
from cdqai.kentucky.systems import TrafficRecordSystem


def _key(value: object) -> str:
    if pd.isna(value):
        return ""
    result = str(value).strip()
    if re.fullmatch(r"[+-]?\d+\.0+", result):
        result = result.split(".", 1)[0]
    return result


def _code(value: object) -> str:
    value = _key(value)
    return value.zfill(2) if value.isdigit() else value.upper()


def _training_path(config: CDQAIConfig) -> Path:
    configured = str(config.raw.get("scooter_classifier", {}).get("training_file", "")).strip()
    if not configured:
        raise ValueError("Set scooter_classifier.training_file to a private, local labeled CSV.")
    path = Path(configured).expanduser()
    if not path.is_absolute():
        path = config.project_root / path
    if not path.is_file():
        raise FileNotFoundError(f"Local scooter training file not found: {path}")
    return path


def _fit_classifier(config: CDQAIConfig) -> tuple[TfidfVectorizer, LogisticRegression, float]:
    cfg = config.raw["scooter_classifier"]
    path = _training_path(config)
    text_field = str(cfg.get("training_text_field", "Narrative"))
    label_field = str(cfg.get("training_label_field", "Scooter"))
    training = pd.read_csv(path, usecols=[text_field, label_field], dtype="string")
    if training.empty:
        raise ValueError("Scooter training CSV has no labeled rows.")
    if training[[text_field, label_field]].isna().any().any():
        raise ValueError("Scooter training CSV contains missing narratives or labels.")
    normalized_text = training[text_field].str.casefold().str.split().str.join(" ")
    if normalized_text.eq("").any():
        raise ValueError("Scooter training CSV contains blank narratives.")

    positive = str(cfg.get("positive_label", "1")).strip()
    negative = str(cfg.get("negative_label", "0")).strip()
    labels = training[label_field].str.strip()
    if positive == negative:
        raise ValueError("Scooter positive_label and negative_label must be distinct.")
    unexpected = sorted(set(labels) - {positive, negative})
    if unexpected:
        raise ValueError(f"Scooter training CSV contains labels outside the configured binary classes: {unexpected}")
    if set(labels) != {positive, negative}:
        raise ValueError("Scooter training CSV must contain examples for both configured binary labels.")
    y = labels.map({negative: 0, positive: 1}).astype(int)
    groups = normalized_text
    label_counts_by_text = pd.DataFrame({"group": groups, "label": y}).groupby("group")["label"].nunique()
    if label_counts_by_text.gt(1).any():
        raise ValueError("Identical normalized narratives have conflicting scooter labels.")
    distinct_groups = pd.DataFrame({"group": groups, "label": y}).drop_duplicates()
    if distinct_groups["label"].value_counts().min() < 5:
        raise ValueError("Scooter training CSV needs at least five distinct narratives in each class for a holdout check.")

    state = int(cfg.get("random_state", 42))
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=state)
    train_idx, test_idx = next(splitter.split(training, y, groups))
    threshold = float(cfg.get("minimum_validation_precision", 0.5))
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("scooter_classifier.minimum_validation_precision must be between 0 and 1.")

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
    train_text = training.iloc[list(train_idx)][text_field].astype(str)
    test_text = training.iloc[list(test_idx)][text_field].astype(str)
    train_y, test_y = y.iloc[list(train_idx)], y.iloc[list(test_idx)]
    train_matrix = vectorizer.fit_transform(train_text)
    validation_model = LogisticRegression(
        class_weight="balanced", max_iter=1000, random_state=state
    ).fit(train_matrix, train_y)
    precision = float(precision_score(
        test_y, validation_model.predict(vectorizer.transform(test_text)), zero_division=0
    ))
    if precision < threshold:
        raise ValueError(
            f"Scooter classifier holdout precision {precision:.3f} is below the configured "
            f"minimum {threshold:.3f}; review labels and thresholds before use."
        )

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
    full_matrix = vectorizer.fit_transform(training[text_field].astype(str))
    classifier = LogisticRegression(
        class_weight="balanced", max_iter=1000, random_state=state
    ).fit(full_matrix, y)
    return vectorizer, classifier, precision


def build_scooter_evidence(
    dataset: CrashDataset, config: CDQAIConfig
) -> tuple[EvidenceCollection, pd.DataFrame, dict[str, float | int]]:
    cfg = config.raw.get("scooter_classifier", {})
    if cfg.get("enabled") is not True:
        return EvidenceCollection(items=[]), pd.DataFrame(columns=["MFN", "ModelScore"]), {
            "enabled": 0, "candidate_count": 0
        }

    vectorizer, classifier, validation_precision = _fit_classifier(config)
    merged = dataset.merged
    fields = config.raw["fields"]
    mfn_field = fields["normalized_mfn_field"]
    narrative_field = fields["narrative_text_field"]
    year_field = str(cfg.get("crash_year_field", "YR"))
    if any(field not in merged.columns for field in (mfn_field, narrative_field, year_field)):
        raise KeyError(
            f"Scooter review requires crash fields {mfn_field!r}, {year_field!r}, and {narrative_field!r}."
        )
    vehicles = dataset.vehicle_type_records
    required_vehicle = {"CDQAI_MFN", "CDQAI_YEAR", "CDQAI_UNIT_TYPE"}
    if vehicles is None or not required_vehicle.issubset(vehicles.columns) or vehicles.empty:
        raise ValueError("Projected vehicle unit-type records are required for scooter coding reconciliation.")

    confidence_threshold = float(cfg.get("confidence_threshold", 0.85))
    if not 0.5 < confidence_threshold <= 1.0:
        raise ValueError("scooter_classifier.confidence_threshold must be greater than 0.5 and at most 1.")
    explicit_code = _code(cfg.get("scooter_unit_type_code", "12"))

    narratives = merged[[mfn_field, year_field, narrative_field]].copy()
    narratives["_mfn"] = narratives[mfn_field].map(_key)
    narratives["_year"] = narratives[year_field].map(_key)
    narratives["_text"] = narratives[narrative_field].fillna("").astype(str)
    narratives = narratives[(narratives["_mfn"] != "") & (narratives["_year"] != "")]
    narratives = narratives[narratives["_text"].str.strip() != ""]
    narratives = narratives.sort_values("_text", key=lambda values: values.str.len(), ascending=False)
    narratives = narratives.drop_duplicates(["_mfn", "_year"], keep="first")
    if narratives.empty:
        raise ValueError("No nonblank crash narratives with MFN and year are available for scooter review.")

    vehicle_keys = set()
    for row in vehicles.itertuples(index=False):
        if _code(row.CDQAI_UNIT_TYPE) == explicit_code:
            mfn, year = _key(row.CDQAI_MFN), _key(row.CDQAI_YEAR)
            if mfn and year:
                vehicle_keys.add((mfn, year))

    model_scores = classifier.predict_proba(vectorizer.transform(narratives["_text"]))[:, 1]
    items = []
    output_rows = []
    for (_, row), score in zip(narratives.iterrows(), model_scores):
        if score < confidence_threshold or (row["_mfn"], row["_year"]) in vehicle_keys:
            continue
        value = float(score)
        output_rows.append({"MFN": row["_mfn"], "ModelScore": round(value, 4)})
        items.append(Evidence(
            mfn=row["_mfn"],
            record_type=RecordType.VEHICLE,
            traffic_record_system=TrafficRecordSystem.VEHICLE,
            quality_characteristic=QualityCharacteristic.COMPLETENESS,
            category="Potential Uncoded E-Scooter",
            severity=Severity.LOW,
            confidence=value,
            message=(
                f"The local narrative classifier indicates possible e-scooter involvement "
                f"(model score {value:.3f}), but no matching vehicle unit has configured "
                f"scooter code {explicit_code}. Review the narrative and vehicle coding; "
                "this model score is not a calibrated probability or a confirmed classification."
            ),
            source="MODEL_SCOOTER_NARRATIVE",
            supporting_fields=[narrative_field, str(cfg.get("unit_type_field", "Unit Type Code"))],
            supporting_values={
                "model_score": round(value, 4),
                "score_is_calibrated_probability": False,
                "holdout_precision": round(validation_precision, 4),
                "explicit_scooter_code": explicit_code,
                "year": row["_year"],
            },
        ))

    return (
        EvidenceCollection(items=items),
        pd.DataFrame(output_rows, columns=["MFN", "ModelScore"]),
        {
            "enabled": 1,
            "candidate_count": len(output_rows),
            "holdout_precision": round(validation_precision, 4),
        },
    )
