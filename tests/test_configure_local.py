# CDQAI file version: 2.5.0
from tools.configure_local import configured


def test_setup_preserves_private_source_settings():
    original = {"database": {"server": "FABRICATED"},
                "tables": {"narrative_table": "ExternalCatalog.dbo.Narratives"},
                "fields": {"narrative_text_field": "FakeNarrative"},
                "person_severity": {"enabled": False, "table": "ExternalCatalog.dbo.People"},
                "cache": {"merged_dataset_file": "merged.parquet"}}
    updated = configured(original, "llama3:latest", False)
    assert updated["database"] == original["database"]
    assert updated["tables"] == original["tables"]
    assert updated["fields"] == original["fields"]
    assert updated["person_severity"] == original["person_severity"]
    assert updated["cache"] == original["cache"]
    assert not updated["analyst_guidance"]["enabled"]
    again = configured(updated, "llama3:latest", True)
    assert again["cache"] == updated["cache"]
    assert again["analyst_guidance"]["enabled"]


def test_setup_does_not_change_configured_data_sources_or_cache_names():
    source = {"tables": {"crash_table": "ExternalCatalog.dbo.Crashes"},
              "cache": {"merged_dataset_file": "existing.parquet"}}
    updated = configured(source, "llama3:latest", True)
    assert updated["tables"] == source["tables"]
    assert updated["cache"] == source["cache"]
