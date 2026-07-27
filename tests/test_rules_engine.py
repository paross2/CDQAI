import pandas as pd

from cdqai.core.config import DEFAULT_CONFIG, CDQAIConfig
from cdqai.rules.engine import RuleEngine


class DummyLogger:
    def info(self, *args, **kwargs):
        pass


class DummyDataset:
    def __init__(self, merged):
        self.merged = merged


def test_rule_engine_missing_narrative(tmp_path):
    raw = DEFAULT_CONFIG.copy()
    raw["fields"] = {
        "normalized_mfn_field": "MFN",
        "narrative_text_field": "NarrativeTxt",
    }

    config = CDQAIConfig(raw=raw, project_root=tmp_path)
    df = pd.DataFrame(
        {
            "MFN": ["1", "2"],
            "NarrativeTxt": ["", "Vehicle struck another vehicle."],
        }
    )

    evidence = RuleEngine(config=config, logger=DummyLogger()).run(DummyDataset(df))
    assert len(evidence.items) >= 1
    assert evidence.items[0].mfn == "1"
