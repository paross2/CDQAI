# CDQAI file version: 2.2.5
"""A repeatable local run using only fabricated records and isolated outputs."""
from __future__ import annotations

from copy import deepcopy
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from cdqai.core.config import CDQAIConfig, DEFAULT_CONFIG
from cdqai.core.paths import find_project_root
from cdqai.data.preprocessing import build_dataset


def run_smoke_test(project_root: Path | None = None) -> int:
    # Never read config.yaml, SQL, or an existing crash/embedding cache here.
    root = project_root if project_root is not None else find_project_root()
    raw = deepcopy(DEFAULT_CONFIG)
    raw["fields"] = {
        "normalized_mfn_field": "MFN",
        "narrative_text_field": "NarrativeTxt",
    }
    raw["paths"] = {
        "cache_dir": "outputs/smoke/cache",
        "logs_dir": "outputs/smoke/logs",
        "outputs_dir": "outputs/smoke",
    }
    raw["cache"].update(use_cache=False, write_cache=False)
    raw["context"]["kentucky_dvmt"]["enabled"] = False
    raw["models"]["narrative"]["enabled"] = False
    raw["models"]["ensemble"].update(structured_weight=1.0, narrative_weight=0.0)
    config = CDQAIConfig(raw=raw, project_root=root)
    for directory in (config.cache_dir, config.logs_dir, config.outputs_dir):
        directory.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(42)
    size = 128
    mfns = [f"SYNTHETIC-{index:04d}" for index in range(size)]
    crashes = pd.DataFrame({
        "MFN": mfns,
        "YR": [2024] * size,
        "CollisionDate": [20240615] * size,
        "CountyNumber": rng.integers(1, 121, size),
        "NumberVehicles": rng.integers(1, 5, size),
        "NumberInjured": rng.integers(0, 3, size),
        "InjurySeverity": ["no injury"] * size,
    })
    text = ["Fabricated example: two vehicles made contact at an intersection."] * size
    text[0] = "Fabricated example: an injured driver was transported by ambulance."
    text[1] = ""
    text[2] = "Synthetic short text."
    narratives = pd.DataFrame({"MFN": mfns, "NarrativeTxt": text})
    dataset = build_dataset(crashes, narratives, config, logging.getLogger("cdqai.smoke"))

    from cdqai.main import run_all

    return run_all(config=config, dataset=dataset)
