from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from cdqai import __milestone__, __project_name__, __short_name__, __version__
from cdqai.core.paths import find_project_root


DEFAULT_CONFIG: dict[str, Any] = {
    "project": {
        "name": __project_name__,
        "short_name": __short_name__,
        "version": __version__,
        "milestone": __milestone__,
    },
    "paths": {
        "cache_dir": "cache",
        "logs_dir": "logs",
        "outputs_dir": "outputs",
        "rules_dir": "rules",
    },
    "runtime": {
        "environment": "development",
        "log_level": "INFO",
    },
    "cache": {
        "use_cache": True,
        "write_cache": True,
        "merged_dataset_file": "merged_crash_dataset.parquet",
        "narrative_embeddings_file": "narrative_embeddings.npy",
        "narrative_embedding_index_file": "narrative_embedding_index.json",
    },
    "outputs": {
        "sample_rows": 1000,
        "summary_file": "dataset_summary.csv",
        "sample_file": "merged_sample.csv",
        "manifest_file": "run_manifest.json",
        "model_scores_file": "model_scores.csv",
        "top_model_anomalies_file": "top_model_anomalies.csv",
        "top_model_anomalies_rows": 1000,
        "evidence_file": "evidence.csv",
        "evidence_summary_file": "evidence_summary.csv",
        "findings_file": "findings.csv",
        "findings_summary_file": "findings_summary.csv",
        "actionable_findings_file": "actionable_findings.csv",
        "top_findings_file": "top_findings.csv",
        "top_findings_rows": 100,
        "annual_findings_file": "annual_findings.csv",
        "dashboard_file": "dashboard.html",
        "dashboard_summary_file": "dashboard_summary.csv",
    },
    "models": {
        "structured": {
            "enabled": True,
            "contamination": 0.02,
            "random_state": 42,
            "max_numeric_columns": 80,
        },
        "narrative": {
            "enabled": True,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "batch_size": 256,
            "contamination": 0.02,
            "random_state": 42,
        },
        "ensemble": {
            "structured_weight": 0.5,
            "narrative_weight": 0.5,
        },
    },
    "model_evidence": {
        "structured_percentile": 99.0,
        "narrative_percentile": 99.0,
        "ensemble_percentile": 99.5,
        "high_percentile": 99.75,
        "critical_percentile": 99.9,
        "multi_model_minimum": 2,
    },
    "rules": {
        "enabled": True,
        "missing_narrative": {
            "enabled": True,
        },
        "sparse_narrative": {
            "enabled": True,
            "minimum_length": 40,
        },
        "required_fields": {
            "enabled": True,
            "rec01": ["MFN"],
        },
        "injury_conflict": {
            "enabled": True,
            "injury_field_candidates": [
                "InjurySeverity",
                "Injury_Severity",
                "Injury",
                "Severity",
                "KABCO",
                "INJ_SEV",
                "INJURY_SEVERITY",
                "MostSevereInjury",
            ],
            "no_injury_values": [
                "no injury",
                "none",
                "not injured",
                "property damage only",
                "pdo",
                "0",
                "00",
                "n",
                "no",
            ],
        },
    },
}


def deep_merge_defaults(user_config: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(defaults)

    for key, value in user_config.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge_defaults(value, merged[key])
        else:
            merged[key] = value

    return merged


def apply_application_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    """Ensure app identity comes from code, not stale local config files."""
    raw.setdefault("project", {})
    raw["project"]["name"] = __project_name__
    raw["project"]["short_name"] = __short_name__
    raw["project"]["version"] = __version__
    raw["project"]["milestone"] = __milestone__
    return raw


@dataclass(frozen=True)
class CDQAIConfig:
    raw: dict[str, Any]
    project_root: Path

    @property
    def project_name(self) -> str:
        return self.raw["project"]["name"]

    @property
    def short_name(self) -> str:
        return self.raw["project"]["short_name"]

    @property
    def version(self) -> str:
        return self.raw["project"]["version"]

    @property
    def milestone(self) -> str:
        return self.raw["project"].get("milestone", "")

    @property
    def cache_dir(self) -> Path:
        return self.project_root / self.raw["paths"]["cache_dir"]

    @property
    def logs_dir(self) -> Path:
        return self.project_root / self.raw["paths"]["logs_dir"]

    @property
    def outputs_dir(self) -> Path:
        return self.project_root / self.raw["paths"]["outputs_dir"]

    @property
    def rules_dir(self) -> Path:
        return self.project_root / self.raw["paths"]["rules_dir"]

    @property
    def log_level(self) -> str:
        return self.raw["runtime"].get("log_level", "INFO")

    @property
    def use_cache(self) -> bool:
        return bool(self.raw["cache"].get("use_cache", True))

    @property
    def write_cache(self) -> bool:
        return bool(self.raw["cache"].get("write_cache", True))

    @property
    def merged_cache_path(self) -> Path:
        return self.cache_dir / self.raw["cache"]["merged_dataset_file"]

    @property
    def narrative_embeddings_path(self) -> Path:
        return self.cache_dir / self.raw["cache"]["narrative_embeddings_file"]

    @property
    def narrative_embedding_index_path(self) -> Path:
        return self.cache_dir / self.raw["cache"]["narrative_embedding_index_file"]


def load_config(config_path: str | Path = "config/config.yaml") -> CDQAIConfig:
    project_root = find_project_root()

    requested_path = project_root / config_path
    example_path = project_root / "config/config.example.yaml"

    if requested_path.exists():
        full_path = requested_path
    elif example_path.exists():
        full_path = example_path
        print(
            "WARNING: config/config.yaml not found.\n"
            "Using config/config.example.yaml.\n"
            "Create config/config.yaml before connecting to a real database."
        )
    else:
        raise FileNotFoundError(
            f"No configuration file found. Expected:\n"
            f"  {requested_path}\n"
            f"or\n"
            f"  {example_path}"
        )

    with full_path.open("r", encoding="utf-8") as file:
        user_config = yaml.safe_load(file) or {}

    raw = deep_merge_defaults(user_config, DEFAULT_CONFIG)
    raw = apply_application_metadata(raw)

    config = CDQAIConfig(raw=raw, project_root=project_root)

    for folder in (
        config.cache_dir,
        config.logs_dir,
        config.outputs_dir,
        config.rules_dir,
    ):
        folder.mkdir(parents=True, exist_ok=True)

    return config
