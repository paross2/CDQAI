from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from cdqai.core.config import CDQAIConfig


def get_git_commit(project_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        return None
    return None


def write_run_manifest(
    config: CDQAIConfig,
    runtime_seconds: float,
    dataset_metadata: Any | None = None,
    model_metadata: dict[str, Any] | None = None,
) -> Path:
    manifest_file = config.raw.get("outputs", {}).get("manifest_file", "run_manifest.json")
    manifest_path = config.outputs_dir / manifest_file

    metadata_dict = None
    if dataset_metadata is not None:
        if is_dataclass(dataset_metadata):
            metadata_dict = asdict(dataset_metadata)
        else:
            metadata_dict = dict(dataset_metadata)

    payload = {
        "run_timestamp": datetime.now().isoformat(timespec="seconds"),
        "project": config.project_name,
        "version": config.version,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "git_commit": get_git_commit(config.project_root),
        "runtime_seconds": runtime_seconds,
        "dataset_metadata": metadata_dict,
        "model_metadata": model_metadata,
    }

    manifest_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return manifest_path
