# CDQAI file version: 2.3.5
from copy import deepcopy
import logging
from types import SimpleNamespace

import pandas as pd
import pytest

from cdqai.core.config import DEFAULT_CONFIG
from cdqai.data.person_severity import review_person_severity, severity_evidence, attach_person_severity, quoted_table
from cdqai.findings.severity_context import severity_by_mfn


def config():
    raw = deepcopy(DEFAULT_CONFIG)
    raw["fields"] = {"normalized_mfn_field": "MFN"}
    return SimpleNamespace(raw=raw)


def frames(codes, kabco="O"):
    crashes = pd.DataFrame({"MFN": ["FAKE"], "YR": [2025], "KABCO": [kabco]})
    persons = pd.DataFrame([["FAKE", 1, i + 1, c, 2025] for i, c in enumerate(codes)],
        columns=["Master File", "Unit Number", "Person Number", "Injury Severity", "YR"])
    return crashes, persons


@pytest.mark.parametrize("code", ["09", 9, 9.0, " 09 "])
def test_reconciliation_stays_unresolved_and_does_not_replace_kabco(code):
    crashes, persons = frames([code], "K")
    original = crashes.copy(deep=True)
    review = review_person_severity(crashes, persons, config())
    assert review.iloc[0].Reconciliation09Count == 1
    assert not review.iloc[0].PersonSeverityResolved
    assert review.iloc[0].HighestKnownPersonSeverity == ""
    assert not severity_evidence(review)
    assert severity_by_mfn(crashes, config()) == {"FAKE": "fatal"}
    pd.testing.assert_frame_equal(crashes, original)


@pytest.mark.parametrize("codes,kabco,conflict", [(["01"], "O", True),
    (["05"], "K", True), (["05", "09"], "K", False), (["01", "09"], "O", True),
    (["03"], "C", True), (["04"], "C", False), ([None], "O", False), (["bad"], "O", False)])
def test_discrepancy_policy(codes, kabco, conflict):
    crashes, persons = frames(codes, kabco)
    review = review_person_severity(crashes, persons, config())
    assert bool(review.iloc[0].SeverityDiscrepancy) == conflict
    assert bool(severity_evidence(review)) == conflict


def test_year_and_person_keys_prevent_false_comparisons():
    crashes, persons = frames(["01"])
    persons["YR"] = 2024
    assert review_person_severity(crashes, persons, config()).iloc[0].SeverityReviewStatus == "No matched persons"
    persons["YR"] = 2025
    persons = pd.concat([persons, persons], ignore_index=True)
    review = review_person_severity(crashes, persons, config())
    assert review.iloc[0].SeverityReviewStatus == "Invalid person keys"
    assert not severity_evidence(review)


def test_disabled_never_queries_and_enabled_projects_only_needed_fields(monkeypatch):
    crashes, persons = frames(["09"])
    cfg = config()
    dataset = SimpleNamespace(merged=crashes, person_severity_review=None)
    calls = []
    def read(query, engine):
        calls.append(query)
        return persons
    monkeypatch.setattr(pd, "read_sql", read)
    attach_person_severity(dataset, cfg, logging.getLogger("test"))
    assert not calls
    cfg.raw["person_severity"]["enabled"] = True
    attach_person_severity(dataset, cfg, logging.getLogger("test"), db=SimpleNamespace(engine=None))
    assert len(calls) == 1
    assert "SELECT *" not in calls[0]
    assert "[Injury Severity]" in calls[0]
    assert "[Last Name]" not in calls[0]
    assert len(dataset.merged) == 1
    assert dataset.person_severity_review.iloc[0].Reconciliation09Count == 1


def test_table_identifier_validation():
    with pytest.raises(ValueError):
        quoted_table("db.dbo.table; SELECT 1")
