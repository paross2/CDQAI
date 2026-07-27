from __future__ import annotations

import pandas as pd

from cdqai.core.config import CDQAIConfig
from cdqai.evidence.engine import EvidenceCollection
from cdqai.evidence.objects import Evidence
from cdqai.evidence.severity import Severity
from cdqai.kentucky.quality import QualityCharacteristic
from cdqai.kentucky.records import RecordType
from cdqai.kentucky.systems import TrafficRecordSystem


def _severity(percentile: float, high: float, critical: float) -> Severity:
    if percentile >= critical:
        return Severity.CRITICAL
    if percentile >= high:
        return Severity.HIGH
    return Severity.MEDIUM


def build_model_evidence(scores: pd.DataFrame, config: CDQAIConfig) -> EvidenceCollection:
    """Convert only extreme model scores into analyst-review evidence."""
    cfg = config.raw.get("model_evidence", {})
    mfn_col = config.raw["fields"]["normalized_mfn_field"]
    structured_t = float(cfg.get("structured_percentile", 99.0))
    narrative_t = float(cfg.get("narrative_percentile", 99.0))
    ensemble_t = float(cfg.get("ensemble_percentile", 99.5))
    high_t = float(cfg.get("high_percentile", 99.75))
    critical_t = float(cfg.get("critical_percentile", 99.9))
    multi_t = int(cfg.get("multi_model_minimum", 2))

    items: list[Evidence] = []
    for _, row in scores.iterrows():
        mfn = str(row[mfn_col])
        s_raw = pd.to_numeric(row.get("StructuredScore_pct"), errors="coerce")
        n_raw = pd.to_numeric(row.get("NarrativeScore_pct"), errors="coerce")
        e_raw = pd.to_numeric(
            row.get("ModelConfidence", row.get("ModelEnsembleScore")),
            errors="coerce",
        )
        s = float(s_raw) if pd.notna(s_raw) else None
        n = float(n_raw) if pd.notna(n_raw) else None
        e = float(e_raw) if pd.notna(e_raw) else None
        signals: list[str] = []

        if s is not None and s >= structured_t:
            signals.append("Structured")
            items.append(Evidence(mfn, RecordType.REC01, TrafficRecordSystem.CRASH,
                QualityCharacteristic.ACCURACY, "Structured Anomaly", _severity(s, high_t, critical_t),
                min(s / 100.0, 1.0),
                "The record contains an unusual combination of structured crash variables compared with other records.",
                "MODEL_STRUCTURED", supporting_fields=["StructuredScore_pct"], supporting_values={"percentile": round(s, 4)}))
        if n is not None and n >= narrative_t:
            signals.append("Narrative")
            items.append(Evidence(mfn, RecordType.REC01, TrafficRecordSystem.CRASH,
                QualityCharacteristic.ACCURACY, "Narrative Anomaly", _severity(n, high_t, critical_t),
                min(n / 100.0, 1.0),
                "The narrative is statistically unusual compared with other crash narratives and warrants review.",
                "MODEL_NARRATIVE", supporting_fields=["NarrativeScore_pct"], supporting_values={"percentile": round(n, 4)}))
        if e is not None and e >= ensemble_t:
            signals.append("Ensemble")
            items.append(Evidence(mfn, RecordType.REC01, TrafficRecordSystem.CRASH,
                QualityCharacteristic.ACCURACY, "Ensemble Anomaly", _severity(e, high_t, critical_t),
                min(e / 100.0, 1.0),
                "The combined structured and narrative model score places this record among the most unusual records.",
                "MODEL_ENSEMBLE", supporting_fields=["ModelConfidence"], supporting_values={"percentile": round(e, 4)}))
        if len(signals) >= multi_t:
            p = max(value for value in (s, n, e) if value is not None)
            items.append(Evidence(mfn, RecordType.REC01, TrafficRecordSystem.CRASH,
                QualityCharacteristic.ACCURACY, "Multi-Model Anomaly", _severity(p, high_t, critical_t),
                min(p / 100.0, 1.0),
                f"Multiple analytical models independently flagged this record ({', '.join(signals)}).",
                "MODEL_MULTI_SIGNAL", supporting_fields=signals, supporting_values={"signals": signals}))

    return EvidenceCollection(items=items)
