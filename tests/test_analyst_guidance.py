# CDQAI file version: 2.3.1
from copy import deepcopy
import json
import logging

import pandas as pd
import pytest

from cdqai.core.config import CDQAIConfig, DEFAULT_CONFIG
from cdqai.evidence.engine import EvidenceCollection
from cdqai.evidence.objects import Evidence
from cdqai.evidence.severity import Severity
from cdqai.findings.engine import FindingEngine
from cdqai.kentucky.quality import QualityCharacteristic
from cdqai.kentucky.records import RecordType
from cdqai.kentucky.systems import TrafficRecordSystem
from cdqai.llm.analyst_guidance import LocalOllama, GuidanceUnavailable, add_analyst_guidance
from cdqai.reports.dashboard_report import _findings_table


def setup_case(tmp_path):
    raw = deepcopy(DEFAULT_CONFIG)
    raw["analyst_guidance"].update(enabled=True, model="llama-test:local", local_only_confirmed=True)
    config = CDQAIConfig(raw, tmp_path)
    item = Evidence("FABRICATED-ID-ONLY", RecordType.REC01, TrafficRecordSystem.CRASH,
                    QualityCharacteristic.ACCURACY, "Structured Anomaly", Severity.HIGH,
                    0.99, "Fabricated unusual field combination.", "MODEL_STRUCTURED",
                    supporting_fields=["StructuredScore_pct"], supporting_values={"percentile": 99.5})
    return config, FindingEngine().run(EvidenceCollection(items=[item]))


def fake_service(path, payload=None):
    if path == "/api/status":
        return {"cloud": {"disabled": True}}
    if path == "/api/tags":
        return {"models": [{"name": "llama-test:local", "size": 2_000_000,
                            "details": {"format": "gguf"}, "digest": "synthetic-digest"}]}
    if path == "/api/show":
        return {"model_info": {"general.architecture": "llama"}}
    return {"done": True, "message": {"content": json.dumps({"breadcrumbs": [
        {"evidence_ids": ["E1"], "fields": ["StructuredScore_pct"],
         "text": "Review the model signal and the source record."}]})}}


def test_guidance_is_separate_and_does_not_send_identifier(tmp_path, monkeypatch):
    config, findings = setup_case(tmp_path)
    packets = []
    def request(self, path, payload=None):
        if path == "/api/chat":
            packets.append(json.dumps(payload))
        return fake_service(path, payload)
    monkeypatch.setattr(LocalOllama, "_request", request)
    result, metadata = add_analyst_guidance(findings, config, logging.getLogger("synthetic"))
    assert result[0].explanation == findings[0].explanation
    assert result[0].priority_score == findings[0].priority_score
    assert result[0].evidence == findings[0].evidence
    assert metadata["generated"] == 1
    assert "FABRICATED-ID-ONLY" not in packets[0]
    assert "[E1]" in result[0].llm_guidance


def test_disabled_guidance_never_calls_ollama(tmp_path, monkeypatch):
    config, findings = setup_case(tmp_path)
    config.raw["analyst_guidance"]["enabled"] = False
    def forbidden(*args, **kwargs):
        pytest.fail("Disabled guidance attempted a request")
    monkeypatch.setattr(LocalOllama, "_request", forbidden)
    result, _ = add_analyst_guidance(findings, config, logging.getLogger("synthetic"))
    assert result[0].review_facts
    assert result[0].llm_status == "Disabled"


def test_transport_is_loopback_only_and_rejects_redirects(monkeypatch):
    endpoints = []
    class Connection:
        def __init__(self, host, port, timeout):
            endpoints.append((host, port))
        def request(self, *args, **kwargs):
            pass
        def getresponse(self):
            return type("Response", (), {"status": 302})()
        def close(self):
            pass
    monkeypatch.setattr("cdqai.llm.analyst_guidance.http.client.HTTPConnection", Connection)
    monkeypatch.setenv("HTTP_PROXY", "http://example.invalid:8080")
    client = LocalOllama(dict(model="llama-test:local", local_only_confirmed=True))
    with pytest.raises(GuidanceUnavailable):
        client._request("/api/tags")
    assert endpoints == [("127.0.0.1", 11434)]


@pytest.mark.parametrize("updates", [{"model": "llama:cloud"}, {"model": ""},
                                     {"local_only_confirmed": False}, {"port": 0}])
def test_unsafe_or_incomplete_configuration_rejected(updates):
    cfg = dict(model="llama-test:local", local_only_confirmed=True, port=11434)
    cfg.update(updates)
    with pytest.raises(GuidanceUnavailable):
        LocalOllama(cfg)


@pytest.mark.parametrize("status", [{}, {"cloud": {"disabled": False}}])
def test_cloud_status_required_before_evidence(tmp_path, monkeypatch, status):
    config, findings = setup_case(tmp_path)
    calls = []
    def request(self, path, payload=None):
        calls.append(path)
        return status
    monkeypatch.setattr(LocalOllama, "_request", request)
    result, _ = add_analyst_guidance(findings, config, logging.getLogger("synthetic"))
    assert calls == ["/api/status"]
    assert result[0].llm_status == "Unavailable"


def test_cloud_alias_is_rejected_before_any_evidence_sent(tmp_path, monkeypatch):
    config, findings = setup_case(tmp_path)
    calls = []
    def request(self, path, payload=None):
        calls.append(path)
        if path == "/api/show":
            return {"remote_host": "https://example.invalid", "model_info": {"general.architecture": "llama"}}
        return fake_service(path, payload)
    monkeypatch.setattr(LocalOllama, "_request", request)
    result, _ = add_analyst_guidance(findings, config, logging.getLogger("synthetic"))
    assert "/api/chat" not in calls
    assert result[0].llm_status == "Unavailable"


def test_invalid_evidence_references_fall_back_without_logging_response(tmp_path, monkeypatch, caplog):
    config, findings = setup_case(tmp_path)
    def request(self, path, payload=None):
        if path == "/api/chat":
            return {"done": True, "message": {"content": json.dumps({"breadcrumbs": [
                {"evidence_ids": ["INVENTED"], "fields": [], "text": "FABRICATED-RESPONSE-SECRET"}]})}}
        return fake_service(path, payload)
    monkeypatch.setattr(LocalOllama, "_request", request)
    result, _ = add_analyst_guidance(findings, config, logging.getLogger("synthetic"))
    assert result[0].llm_guidance == ""
    assert result[0].explanation == findings[0].explanation
    assert "FABRICATED-RESPONSE-SECRET" not in caplog.text


def test_dashboard_escapes_generated_text(tmp_path, monkeypatch):
    config, findings = setup_case(tmp_path)
    def request(self, path, payload=None):
        response = fake_service(path, payload)
        if path == "/api/chat":
            response["message"]["content"] = json.dumps({"breadcrumbs": [
                {"evidence_ids": ["E1"], "fields": [], "text": "<script>fake()</script>"}]})
        return response
    monkeypatch.setattr(LocalOllama, "_request", request)
    result, _ = add_analyst_guidance(findings, config, logging.getLogger("synthetic"))
    rendered = _findings_table(pd.DataFrame([result[0].to_dict()]))
    assert "<script>fake()" not in rendered
    assert "&lt;script&gt;fake()" in rendered
    assert "Recorded triggers and fields worth checking" in rendered


def test_rejected_draft_does_not_cancel_other_findings(tmp_path, monkeypatch):
    from dataclasses import replace
    config, findings = setup_case(tmp_path)
    findings.append(replace(findings[0], mfn="SECOND-FABRICATED"))
    calls = []
    def request(self, path, payload=None):
        if path == "/api/chat":
            calls.append(payload)
            if len(calls) == 1:
                return {"done": True, "message": {"content": "invalid JSON"}}
        return fake_service(path, payload)
    monkeypatch.setattr(LocalOllama, "_request", request)
    result, metadata = add_analyst_guidance(findings, config, logging.getLogger("synthetic"))
    assert result[0].llm_status == "Unavailable (draft_rejected)"
    assert result[1].llm_guidance
    assert metadata["generated"] == metadata["unavailable"] == 1
    props = calls[0]["format"]["properties"]["breadcrumbs"]["items"]["properties"]
    assert props["evidence_ids"]["items"]["enum"] == ["E1"]


def test_timeout_is_safe_and_remaining_findings_are_not_attempted(tmp_path, monkeypatch, caplog):
    from dataclasses import replace
    config, findings = setup_case(tmp_path)
    findings.append(replace(findings[0], mfn="SECOND-FABRICATED"))
    def request(self, path, payload=None):
        if path == "/api/chat":
            raise GuidanceUnavailable("DO-NOT-LOG-THIS", "timeout")
        return fake_service(path, payload)
    monkeypatch.setattr(LocalOllama, "_request", request)
    result, _ = add_analyst_guidance(findings, config, logging.getLogger("synthetic"))
    assert result[0].llm_status == "Unavailable (timeout)"
    assert result[1].llm_status == "Not attempted after timeout"
    assert "DO-NOT-LOG-THIS" not in caplog.text
