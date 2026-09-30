# CDQAI file version: 2.3.1
from tools.configure_local import configured


def test_setup_preserves_private_settings_and_invalidates_old_caches():
    original = {"database": {"server": "FABRICATED"}, "tables": {"narrative_table": "FAKE"},
                "fields": {"narrative_text_field": "FakeNarrative"}}
    updated = configured(original, "llama3:latest", False)
    assert updated["database"] == original["database"]
    assert updated["tables"]["narrative_table"] == "Bill.dbo.NarrativesRepaired"
    assert updated["fields"]["narrative_text_field"] == "FakeNarrative"
    assert updated["person_severity"]["enabled"]
    assert not updated["analyst_guidance"]["enabled"]
    assert "cache" not in original
    again = configured(updated, "llama3:latest", True)
    assert again["cache"] == updated["cache"]
    assert again["analyst_guidance"]["enabled"]


def test_switching_only_narrative_source_refreshes_all_model_caches():
    ready = configured({"tables": {}, "fields": {}}, "llama3:latest", True)
    ready["tables"]["narrative_table"] = "KTC_Crash.dbo.NarrativesRepaired"
    changed = configured(ready, "llama3:latest", True)
    assert changed["tables"]["narrative_table"] == "Bill.dbo.NarrativesRepaired"
    for name in ("merged_dataset_file", "narrative_embeddings_file", "narrative_embedding_index_file"):
        assert changed["cache"][name] != ready["cache"][name]
    assert configured(changed, "llama3:latest", True)["cache"] == changed["cache"]
