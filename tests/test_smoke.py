# CDQAI file version: 2.5.1
import pandas as pd
import json
import pytest

from cdqai import main
from cdqai.smoke import run_smoke_test
from cdqai.core.build_info import VERSION


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
    assert findings["IssueCategories"].str.contains("Structured Anomaly").any()
    assert findings["CrashSeverityGroup"].ne("unknown").all()
    assert findings["LLMStatus"].eq("Disabled").all()
    for name in ("dashboard.html", "dashboard_findings_index.js", "run_manifest.json"):
        assert (output / name).is_file()
    index_text = (output / "dashboard_findings_index.js").read_text(encoding="utf-8")
    index = json.loads(index_text.removeprefix("window.CDQAIAllFindings = ").strip().removesuffix(";"))
    assert len(index["records"]) == len(findings)
    detail_files = sorted(output.glob("dashboard_finding_details_*.js"))
    assert detail_files
    payload = {}
    for detail_file in detail_files:
        detail_text = detail_file.read_text(encoding="utf-8")
        chunk_text = detail_text.split("] = ", 1)[1].strip().removesuffix(";")
        payload.update(json.loads(chunk_text)["narratives"])
    assert any(row["evidenceSpans"] for row in payload.values())
    dashboard = (output / "dashboard.html").read_text(encoding="utf-8")
    assert json.loads((output / "run_manifest.json").read_text())["version"] == VERSION
    assert f"<title>CDQAI {VERSION}</title>" in dashboard
    assert f"Evidence and Review Dashboard \u2014 Version {VERSION}" in dashboard
    assert f"Version {VERSION} \u00b7 Kentucky Transportation Center" in dashboard
    assert 'data-narrative-status="highlighted"' in dashboard
    assert 'Finding MFNs with yellow narrative highlights' in dashboard
    assert 'id="print-flagged"' in dashboard
    assert 'const flaggedCrashes = new Set()' in dashboard
    assert 'class="pagination-controls"' in dashboard
    for row in payload.values():
        for span in row["evidenceSpans"]:
            assert row["narrativeFull"][span["start"]:span["end"]] == span["text"]


def test_smoke_cannot_be_combined_with_a_real_run():
    with pytest.raises(SystemExit) as error:
        main.main(["--smoke-test", "--run-all"])
    assert error.value.code == 2
