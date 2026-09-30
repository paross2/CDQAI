# CDQAI file version: 2.3.1
"""User-run setup only. Never invoke against private configuration from an AI tool."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys
import uuid

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cdqai.llm.analyst_guidance import LocalOllama


def configured(raw, model, guidance_ready):
    result = deepcopy(raw)
    tables = result.setdefault("tables", {})
    fields = result.setdefault("fields", {})
    changed = (tables.get("crash_table") != "MultiYear.dbo.Rec01_2021to2025"
               or tables.get("narrative_table") != "Bill.dbo.NarrativesRepaired"
               or fields.get("crash_mfn_field") != "MasterFile"
               or not result.get("person_severity", {}).get("enabled"))
    tables["crash_table"] = "MultiYear.dbo.Rec01_2021to2025"
    tables["narrative_table"] = "Bill.dbo.NarrativesRepaired"
    fields["crash_mfn_field"] = "MasterFile"
    result["person_severity"] = {"enabled": True, "table": "MultiYear.dbo.Rec03_2021to2025"}
    priority = result.setdefault("review_priority", {})
    priority["severity_field"] = "KABCO"
    priority["severity_codes"] = {"fatal": ["K"], "serious_injury": ["A"],
                                 "other_injury": ["B", "C"], "property_damage": ["O"]}
    guidance = result.setdefault("analyst_guidance", {})
    guidance.update(enabled=guidance_ready, local_only_confirmed=guidance_ready,
                    model=model, port=11434, max_findings=20, timeout_seconds=180)
    if changed:
        # New names bypass old-period caches without deleting any local artifacts.
        suffix = uuid.uuid4().hex[:12]
        result.setdefault("cache", {}).update(
            merged_dataset_file=f"merged_2021to2025_{suffix}.parquet",
            narrative_embeddings_file=f"embeddings_2021to2025_{suffix}.npy",
            narrative_embedding_index_file=f"embedding_index_2021to2025_{suffix}.json")
    return result


def disable_cloud():
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
        winreg.SetValueEx(key, "OLLAMA_NO_CLOUD", 0, winreg.REG_SZ, "1")
    os.environ["OLLAMA_NO_CLOUD"] = "1"
    # Notify Windows so a newly launched Ollama inherits the updated setting.
    import ctypes
    result = ctypes.c_size_t()
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment",
                                            0x0002, 5000, ctypes.byref(result))


def save_config(path, result):
    backup_dir = ROOT / "outputs" / "private-config-backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    (backup_dir / f"config-{token}.yaml").write_bytes(path.read_bytes())
    # Temporary and backup files stay in an ignored folder, not alongside config.yaml.
    temporary = backup_dir / f"pending-{token}.yaml"
    temporary.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
    os.replace(temporary, path)


def main():
    print("CDQAI optional-feature setup (no crash data is loaded)")
    print("This selects Rec01/Rec03 2021-2025 and Bill.dbo.NarrativesRepaired,")
    print("preserves connection and narrative-column settings,")
    print("backs up private configuration under ignored outputs, and disables Ollama cloud.")
    print("YAML comments/formatting will be replaced; the original is backed up.")
    if input("Apply these local settings? [y/N]: ").strip().lower() != "y":
        return 0
    path = ROOT / "config" / "config.yaml"
    if not path.is_file():
        print("Create your private config/config.yaml first using How To Run.txt.")
        return 1
    model = input("Installed local Llama tag [llama3:latest]: ").strip() or "llama3:latest"
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
        if not isinstance(raw, dict):
            raise ValueError
        disable_cloud()
        ready = False
        try:
            client = LocalOllama(dict(model=model, port=11434, timeout_seconds=10,
                                     local_only_confirmed=True))
            client.verify_model()  # Metadata only. No prompt, download, or generation.
            ready = True
        except Exception:
            pass
        save_config(path, configured(raw, model, ready))
    except Exception:
        # Never print YAML parser exceptions, credentials, or configuration contents.
        print("Setup could not finish. Inspect configuration locally; no details were logged.")
        return 1
    print("Rec03 comparison enabled. KABCO remains the priority source.")
    if not ready:
        print("Llama guidance is OFF until the local-only model check passes.")
        print("Quit Ollama from its taskbar icon, reopen it from Start, then rerun this setup.")
        print("If still unavailable, check the installed model tag and update Ollama locally.")
    else:
        print("Local-only server/model verification passed. Llama guidance enabled.")
        print("Run Run_CDQAI.bat yourself and inspect outputs/dashboard.html privately.")
    print("Narrative source: Bill.dbo.NarrativesRepaired. Changed sources receive fresh cache names.")
    print("Missing 2025 source narratives will remain unavailable until supplied in SQL Server.")
    print("Backups and generated outputs are private: do not commit or upload them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
