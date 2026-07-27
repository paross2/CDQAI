from copy import deepcopy

from cdqai.core.config import CDQAIConfig, load_config
from cdqai.reports.dashboard_report import build_how_cdqai_works_html


def _with_thresholds(**updates: float) -> CDQAIConfig:
    config = load_config()
    raw = deepcopy(config.raw)
    raw["model_evidence"].update(updates)
    return CDQAIConfig(raw=raw, project_root=config.project_root)


def test_dashboard_documentation_uses_active_thresholds():
    config = _with_thresholds(
        structured_percentile=98.25,
        narrative_percentile=98.5,
        ensemble_percentile=99.25,
        high_percentile=99.6,
        critical_percentile=99.95,
    )

    explanation = build_how_cdqai_works_html(config)

    assert "98.25th percentile" in explanation
    assert "98.5th percentile" in explanation
    assert "99.25th percentile" in explanation
    assert "99.6th percentile" in explanation
    assert "99.95th percentile" in explanation


def test_dashboard_documentation_discloses_deterministic_synthesis():
    explanation = build_how_cdqai_works_html(load_config())

    assert "deterministic Finding Engine" in explanation
    assert "does not use Llama or another large language model" in explanation
    assert "Uses Llama" not in explanation
    assert "LLM performs synthesis" not in explanation
