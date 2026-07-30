from cdqai.reports.dashboard_report import _highlight_narrative


def test_rule_terms_are_highlighted_safely():
    rendered = _highlight_narrative(
        "The driver was AIRLIFTED to the hospital after an injury.",
        "airlifted; hospital; injury",
    )
    assert "<mark>AIRLIFTED</mark>" in rendered
    assert "<mark>hospital</mark>" in rendered
    assert "deterministic rule" in rendered


def test_embedding_only_narrative_has_no_false_attribution():
    rendered = _highlight_narrative("An unusual but valid narrative.", "")
    assert "<mark>" not in rendered
    assert "statistically unusual as a whole" in rendered


def test_narrative_html_is_escaped():
    rendered = _highlight_narrative("<script>alert(1)</script>", "")
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
