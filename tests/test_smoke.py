# CDQAI file version: 2.2.5
import pandas as pd
import pytest

from cdqai import main
from cdqai.smoke import run_smoke_test


def test_smoke_is_isolated_from_private_config_and_data(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Synthetic smoke run tried to load private configuration or data")

    monkeypatch.setattr(main, "load_config", forbidden)
    monkeypatch.setattr(main, "load_dataset", forbidden)
    assert run_smoke_test(tmp_path) == 0
    output = tmp_path / "outputs/smoke"
    scores = pd.read_csv(output / "model_scores.csv")
    findings = pd.read_csv(output / "findings.csv")
    assert len(scores) == 128
    assert scores["MFN"].str.startswith("SYNTHETIC-").all()
    assert findings["CrashYear"].eq(2024).all()
    assert findings["IssueCategories"].str.contains("Narrative Injury Conflict").any()
    for name in ("dashboard.html", "dashboard_narratives.js", "run_manifest.json"):
        assert (output / name).is_file()


def test_smoke_cannot_be_combined_with_a_real_run():
    with pytest.raises(SystemExit) as error:
        main.main(["--smoke-test", "--run-all"])
    assert error.value.code == 2
