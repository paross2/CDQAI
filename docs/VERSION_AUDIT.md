<!-- CDQAI file version: 2.3.6 -->
# Version audit - 2026-10-01

Audit baseline: commit `0934052`, published software release **2.3.5**.
This is an audit snapshot; historical numbers in this document are intentional.

## Findings

- All 133 maintained files at the start of the audit had the correct 2.3.5 distribution marker. There were 178 Git-tracked files total: 133 maintained files, 16 additional historical documents, and 29 external workbooks. Workbook contents and private outputs were not read.
- `VERSION`, runtime metadata, package metadata, citation, and example configuration all said 2.3.5. No current dashboard template hardcodes 2.3.2.
- The supplied screenshot says 2.3.2. This establishes the displayed report's label, not which installation produced it. An older generated report or a different installation is consistent with the evidence. Private reports and configuration were not inspected, and the exact cause is not proven.
- The launcher runs Python relative to its own directory. Updating this Git checkout or publishing a GitHub release cannot update a separate installation or existing HTML.
- A failed real-data run can leave an earlier HTML report in place. Offline HTML has no live link to the repository's latest release.
- Current-use `docs/ANALYST_GUIDANCE.md` still said Version 2.3.2; `docs/NARRATIVE_HIGHLIGHTS.md` had a 2.3.0 heading. Corrected both and extended synchronization coverage.
- The previous check could miss files absent from its inventory. Added an explicit exclusion inventory and `--check-git` to classify every tracked filename without opening external data.
- The previous updater did not refresh the README release-note link. It now does; release names and new notes remain explicit checklist steps.
- Existing historical release-note bodies and changelogs correctly retain older numbers. Some archived notes also have current distribution markers; these identify the distributed file, not the release described by its body.
- GitHub file/folder last-commit labels, OS/Python/dependency versions, citation schema version, test-fixture versions, and dataset years are not application release labels.

## Version propagation and preflight ownership

| Point | Source and policy | Required verification |
| --- | --- | --- |
| Release source | `VERSION` | Chosen unused release number |
| Runtime and fallback tag | `cdqai/core/build_info.py` VERSION / DEFAULT_TAG | Match VERSION; release name reviewed separately |
| Public package API | `cdqai/__init__.py` re-exports build metadata | Import from intended installation |
| Configuration | `cdqai/core/config.py` defaults and apply_application_metadata | Stale local version is overwritten by running code |
| Package distribution | `pyproject.toml` project.version | Matches VERSION |
| Citation | `CITATION.cff` version/date-released | Software version and date, not cff-version |
| Launchers | Run_CDQAI.bat / Release_CDQAI.bat read VERSION | Directory printed; source check passes |
| Logs | `cdqai/main.py` log_banner reads config.version | Local run version and project root |
| Manifest | `cdqai/core/manifest.py` writes config.version | Synthetic manifest matches VERSION |
| Dashboard title/header/footer | `cdqai/reports/dashboard_report.py` uses config.version | Synthetic HTML labels match VERSION |
| Dashboard project/provenance/help | Same template; collect_build_info uses build VERSION | Same version and release name |
| Dashboard timestamp | Generation time in HTML/build metadata | New successful run, not browser opening time |
| Narrative companion | Generated alongside HTML, no independent release label | Keep files from the same run; expand a synthetic finding |
| Selected-crash PDF | `cdqai/reports/review_selection.py` copies document.title into report metadata | Inherits originating dashboard version |
| Current documentation | README, installation/run guides, analyst/narrative guides | Body references and links, not only markers |
| Every maintained file | release-files.txt / with_marker | --check passes |
| Every Git path | release-files.txt or release-exclusions.txt | --check-git passes; new staged files rechecked |
| Historical/external references | Historical notes, changelogs, fixtures, dependencies, datasets | Preserve original meaning |
| Git tag and GitHub release | Published tag, commit, release title/notes/Latest | Verify after publication; never move published tags |
| Installed output | User's actual checkout and generated report | Path, version, timestamp and successful local regeneration |

See [RELEASE_PREFLIGHT.md](RELEASE_PREFLIGHT.md) for the operational checklist.
This audit does not claim that a newly generated report is already installed on the user's other checkouts.

## Every tracked file at audit baseline

`Maintained` means its distribution marker is checked; runtime/current-use values receive the additional checks above. `Historical` preserves body references. `External` means filename-only classification, with contents excluded from the audit.

| File | Policy |
| --- | --- |
| `.gitignore` | Maintained |
| `AGENTS.md` | Maintained |
| `AUTHORS.md` | Maintained |
| `CHANGELOG.md` | Maintained |
| `CITATION.cff` | Maintained |
| `Check_Local_Llama.bat` | Maintained |
| `Configure_CDQAI.bat` | Maintained |
| `GIT_SETUP.md` | Maintained |
| `How To Run.txt` | Maintained |
| `INSTALL.txt` | Maintained |
| `LICENSE` | Maintained |
| `LICENSE-DOCS` | Maintained |
| `README.md` | Maintained |
| `Release_CDQAI.bat` | Maintained |
| `Run_CDQAI.bat` | Maintained |
| `VERSION` | Maintained |
| `cache/.gitkeep` | Maintained |
| `cdqai/__init__.py` | Maintained |
| `cdqai/classifiers/__init__.py` | Maintained |
| `cdqai/context/__init__.py` | Maintained |
| `cdqai/context/dvmt.py` | Maintained |
| `cdqai/core/__init__.py` | Maintained |
| `cdqai/core/build_info.py` | Maintained |
| `cdqai/core/config.py` | Maintained |
| `cdqai/core/logger.py` | Maintained |
| `cdqai/core/manifest.py` | Maintained |
| `cdqai/core/paths.py` | Maintained |
| `cdqai/core/timing.py` | Maintained |
| `cdqai/dashboard/__init__.py` | Maintained |
| `cdqai/data/__init__.py` | Maintained |
| `cdqai/data/cache.py` | Maintained |
| `cdqai/data/database.py` | Maintained |
| `cdqai/data/dataset.py` | Maintained |
| `cdqai/data/person_severity.py` | Maintained |
| `cdqai/data/preprocessing.py` | Maintained |
| `cdqai/detectors/__init__.py` | Maintained |
| `cdqai/detectors/embeddings.py` | Maintained |
| `cdqai/detectors/model_runner.py` | Maintained |
| `cdqai/detectors/narrative.py` | Maintained |
| `cdqai/detectors/narrative_spans.py` | Maintained |
| `cdqai/detectors/structured.py` | Maintained |
| `cdqai/evidence/__init__.py` | Maintained |
| `cdqai/evidence/bundle.py` | Maintained |
| `cdqai/evidence/engine.py` | Maintained |
| `cdqai/evidence/model_evidence.py` | Maintained |
| `cdqai/evidence/objects.py` | Maintained |
| `cdqai/evidence/severity.py` | Maintained |
| `cdqai/explain/__init__.py` | Maintained |
| `cdqai/features/__init__.py` | Maintained |
| `cdqai/features/field_roles.py` | Maintained |
| `cdqai/findings/__init__.py` | Maintained |
| `cdqai/findings/decision_support.py` | Maintained |
| `cdqai/findings/engine.py` | Maintained |
| `cdqai/findings/finding.py` | Maintained |
| `cdqai/findings/priority.py` | Maintained |
| `cdqai/findings/review_facts.py` | Maintained |
| `cdqai/findings/severity_context.py` | Maintained |
| `cdqai/findings/types.py` | Maintained |
| `cdqai/kentucky/__init__.py` | Maintained |
| `cdqai/kentucky/mapping.py` | Maintained |
| `cdqai/kentucky/quality.py` | Maintained |
| `cdqai/kentucky/records.py` | Maintained |
| `cdqai/kentucky/systems.py` | Maintained |
| `cdqai/llm/__init__.py` | Maintained |
| `cdqai/llm/analyst_guidance.py` | Maintained |
| `cdqai/main.py` | Maintained |
| `cdqai/models/__init__.py` | Maintained |
| `cdqai/reports/__init__.py` | Maintained |
| `cdqai/reports/dashboard_report.py` | Maintained |
| `cdqai/reports/dataset_report.py` | Maintained |
| `cdqai/reports/evidence_report.py` | Maintained |
| `cdqai/reports/field_manifest.py` | Maintained |
| `cdqai/reports/finding_report.py` | Maintained |
| `cdqai/reports/model_report.py` | Maintained |
| `cdqai/reports/review_selection.py` | Maintained |
| `cdqai/rules/__init__.py` | Maintained |
| `cdqai/rules/base.py` | Maintained |
| `cdqai/rules/completeness.py` | Maintained |
| `cdqai/rules/engine.py` | Maintained |
| `cdqai/rules/injury.py` | Maintained |
| `cdqai/rules/narrative_quality.py` | Maintained |
| `cdqai/smoke.py` | Maintained |
| `config/config.example.yaml` | Maintained |
| `context/kentucky_dvmt/README.md` | Maintained |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT1997.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT1998.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT1999.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2000.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2001.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2002.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2003.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2004.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2005.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2006.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2007.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2008.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2009.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2010.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2011.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2012.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2013.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2014.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2015.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2016.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2017.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2018.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2019.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2020.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2021.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2022.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2023.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2024.xlsx` | External |
| `context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2025.xlsx` | External |
| `docs/ANALYST_GUIDANCE.md` | Maintained |
| `docs/ARCHITECTURE.md` | Maintained |
| `docs/CDQAI_DESIGN.md` | Maintained |
| `docs/CHANGELOG.md` | Maintained |
| `docs/DEVELOPMENT.md` | Maintained |
| `docs/DEVELOPMENT_REVIEW.md` | Historical |
| `docs/NARRATIVE_HIGHLIGHTS.md` | Maintained |
| `docs/PERSON_SEVERITY.md` | Maintained |
| `docs/RELEASE_NOTES_2.0.0.md` | Historical |
| `docs/RELEASE_NOTES_2.0.1.md` | Historical |
| `docs/RELEASE_NOTES_2.0.2.md` | Historical |
| `docs/RELEASE_NOTES_2.1.0.md` | Historical |
| `docs/RELEASE_NOTES_2.1.1.md` | Historical |
| `docs/RELEASE_NOTES_2.1.2.md` | Historical |
| `docs/RELEASE_NOTES_2.2.0.md` | Historical |
| `docs/RELEASE_NOTES_2.2.1.md` | Historical |
| `docs/RELEASE_NOTES_2.2.2.md` | Historical |
| `docs/RELEASE_NOTES_2.2.3.md` | Historical |
| `docs/RELEASE_NOTES_2.2.4.md` | Historical |
| `docs/RELEASE_NOTES_2.2.5.md` | Historical |
| `docs/RELEASE_NOTES_2.3.0.md` | Maintained |
| `docs/RELEASE_NOTES_2.3.1.md` | Maintained |
| `docs/RELEASE_NOTES_2.3.2.md` | Maintained |
| `docs/RELEASE_NOTES_2.3.5.md` | Maintained |
| `docs/ROADMAP.md` | Maintained |
| `docs/TECHNICAL_ARCHITECTURE.md` | Maintained |
| `docs/USER_GUIDE.md` | Maintained |
| `docs/VERSION_1_5_0.md` | Historical |
| `docs/history/INSTALL_VERSION_2.0.1.txt` | Historical |
| `docs/history/INSTALL_VERSION_2.0.txt` | Historical |
| `logs/.gitkeep` | Maintained |
| `outputs/.gitkeep` | Maintained |
| `pyproject.toml` | Maintained |
| `release-files.txt` | Maintained |
| `requirements-dev.txt` | Maintained |
| `requirements.txt` | Maintained |
| `run_cdqai.py` | Maintained |
| `tests/test_analyst_guidance.py` | Maintained |
| `tests/test_build_info.py` | Maintained |
| `tests/test_config.py` | Maintained |
| `tests/test_configure_local.py` | Maintained |
| `tests/test_context_dvmt.py` | Maintained |
| `tests/test_dashboard_documentation.py` | Maintained |
| `tests/test_dashboard_external_narratives.py` | Maintained |
| `tests/test_dashboard_highlight_pipeline.py` | Maintained |
| `tests/test_dashboard_interactivity.py` | Maintained |
| `tests/test_dashboard_mfn_normalization.py` | Maintained |
| `tests/test_dashboard_narrative_evidence.py` | Maintained |
| `tests/test_decision_support.py` | Maintained |
| `tests/test_evidence.py` | Maintained |
| `tests/test_kentucky_mapping.py` | Maintained |
| `tests/test_model_evidence.py` | Maintained |
| `tests/test_narrative_availability.py` | Maintained |
| `tests/test_narrative_spans.py` | Maintained |
| `tests/test_paths.py` | Maintained |
| `tests/test_person_severity.py` | Maintained |
| `tests/test_preprocessing.py` | Maintained |
| `tests/test_release_version.py` | Maintained |
| `tests/test_review_priority.py` | Maintained |
| `tests/test_rules_engine.py` | Maintained |
| `tests/test_smoke.py` | Maintained |
| `tests/test_structured_detector.py` | Maintained |
| `tools/check_synthetic_ollama.py` | Maintained |
| `tools/configure_local.py` | Maintained |
| `tools/release_version.py` | Maintained |

## New audit files

- `docs/VERSION_AUDIT.md`: this dated audit snapshot.
- `docs/RELEASE_PREFLIGHT.md`: maintained checklist.
- `release-exclusions.txt`: exact historical/external filename exclusions.

## Non-marker version literals

Reference locations below were scanned during this audit. Earlier sections distinguish current labels from intentional history and non-application versions. Dynamic labels are mapped above. Line numbers may shift with later edits.

| Location | Version literals |
| --- | --- |
| `CHANGELOG.md:4` | `2.3.5` |
| `CHANGELOG.md:6` | `2.3.2` |
| `CHANGELOG.md:10` | `2.3.5` |
| `CHANGELOG.md:12` | `2.3.2` |
| `CHANGELOG.md:18` | `2.3.1` |
| `CHANGELOG.md:20` | `2.3.0`, `2.3.1` |
| `CHANGELOG.md:22` | `2.3.1` |
| `CHANGELOG.md:24` | `2.3.0` |
| `CHANGELOG.md:55` | `v2.2.5` |
| `CHANGELOG.md:57` | `2.2.5` |
| `CHANGELOG.md:68` | `2.2.4` |
| `CHANGELOG.md:75` | `2.2.3` |
| `CHANGELOG.md:84` | `2.2.2` |
| `CHANGELOG.md:90` | `2.2.1` |
| `CHANGELOG.md:101` | `2.2.0` |
| `CHANGELOG.md:113` | `2.1.2` |
| `CHANGELOG.md:122` | `2.1.1` |
| `CHANGELOG.md:132` | `2.0.2` |
| `CHANGELOG.md:146` | `2.0.1` |
| `CHANGELOG.md:151` | `2.0.1` |
| `CHANGELOG.md:153` | `1.4.0` |
| `CHANGELOG.md:167` | `1.3.0` |
| `CHANGELOG.md:178` | `1.2.0` |
| `CHANGELOG.md:189` | `1.1.0` |
| `CHANGELOG.md:201` | `2.0.0` |
| `CHANGELOG.md:208` | `2.1.0` |
| `CITATION.cff:2` | `1.2.0` |
| `CITATION.cff:5` | `2.3.5` |
| `How To Run.txt:4` | `2.3.5` |
| `How To Run.txt:20` | `2.3.5` |
| `INSTALL.txt:2` | `2.3.5` |
| `README.md:4` | `2.3.5` |
| `README.md:12` | `2.3.5` |
| `README.md:110` | `2.3.5` |
| `README.md:163` | `2.3.5` |
| `README.md:167` | `2.3.5` |
| `VERSION:1` | `2.3.5` |
| `cdqai/core/build_info.py:14` | `2.3.5` |
| `cdqai/core/build_info.py:18` | `v2.3.5` |
| `config/config.example.yaml:41` | `2.3.5` |
| `docs/ANALYST_GUIDANCE.md:22` | `2.3.2` |
| `docs/CHANGELOG.md:4` | `2.3.5` |
| `docs/CHANGELOG.md:6` | `2.3.2` |
| `docs/CHANGELOG.md:10` | `2.3.5` |
| `docs/CHANGELOG.md:12` | `2.3.2` |
| `docs/CHANGELOG.md:17` | `2.3.1` |
| `docs/CHANGELOG.md:22` | `2.3.0` |
| `docs/CHANGELOG.md:27` | `2.3.0` |
| `docs/CHANGELOG.md:29` | `2.2.5` |
| `docs/CHANGELOG.md:36` | `2.2.3` |
| `docs/CHANGELOG.md:45` | `2.2.2` |
| `docs/CHANGELOG.md:51` | `2.1.2` |
| `docs/CHANGELOG.md:60` | `2.1.1` |
| `docs/CHANGELOG.md:70` | `2.0.2` |
| `docs/CHANGELOG.md:84` | `2.0.1` |
| `docs/CHANGELOG.md:89` | `2.0.1` |
| `docs/CHANGELOG.md:91` | `1.4.0` |
| `docs/CHANGELOG.md:105` | `1.3.0` |
| `docs/CHANGELOG.md:116` | `1.2.0` |
| `docs/CHANGELOG.md:127` | `1.1.0` |
| `docs/CHANGELOG.md:139` | `2.0.0` |
| `docs/CHANGELOG.md:146` | `2.1.0` |
| `docs/DEVELOPMENT_REVIEW.md:5` | `2.2.4` |
| `docs/DEVELOPMENT_REVIEW.md:7` | `2.2.4` |
| `docs/DEVELOPMENT_REVIEW.md:23` | `2.2.4` |
| `docs/NARRATIVE_HIGHLIGHTS.md:2` | `2.3.5` |
| `docs/RELEASE_NOTES_2.0.0.md:1` | `2.0.0` |
| `docs/RELEASE_NOTES_2.0.1.md:1` | `2.0.1` |
| `docs/RELEASE_NOTES_2.0.1.md:5` | `2.0.1` |
| `docs/RELEASE_NOTES_2.0.1.md:15` | `2.0.1` |
| `docs/RELEASE_NOTES_2.0.1.md:21` | `2.0.1` |
| `docs/RELEASE_NOTES_2.0.2.md:1` | `2.0.2` |
| `docs/RELEASE_NOTES_2.0.2.md:5` | `2.0.2` |
| `docs/RELEASE_NOTES_2.1.0.md:1` | `2.1.0` |
| `docs/RELEASE_NOTES_2.1.0.md:3` | `2.1.0` |
| `docs/RELEASE_NOTES_2.1.1.md:1` | `2.1.1` |
| `docs/RELEASE_NOTES_2.1.1.md:3` | `2.1.1` |
| `docs/RELEASE_NOTES_2.1.2.md:1` | `2.1.2` |
| `docs/RELEASE_NOTES_2.1.2.md:3` | `2.1.2` |
| `docs/RELEASE_NOTES_2.2.0.md:1` | `2.2.0` |
| `docs/RELEASE_NOTES_2.2.0.md:3` | `2.2.0` |
| `docs/RELEASE_NOTES_2.2.1.md:1` | `2.2.1` |
| `docs/RELEASE_NOTES_2.2.1.md:3` | `2.2.1` |
| `docs/RELEASE_NOTES_2.2.2.md:1` | `2.2.2` |
| `docs/RELEASE_NOTES_2.2.2.md:3` | `2.2.2` |
| `docs/RELEASE_NOTES_2.2.2.md:18` | `2.2.2` |
| `docs/RELEASE_NOTES_2.2.3.md:1` | `2.2.3` |
| `docs/RELEASE_NOTES_2.2.3.md:3` | `2.2.3` |
| `docs/RELEASE_NOTES_2.2.4.md:1` | `2.2.4` |
| `docs/RELEASE_NOTES_2.2.4.md:3` | `2.2.4` |
| `docs/RELEASE_NOTES_2.2.5.md:1` | `2.2.5` |
| `docs/RELEASE_NOTES_2.3.0.md:2` | `2.3.0` |
| `docs/RELEASE_NOTES_2.3.1.md:2` | `2.3.1` |
| `docs/RELEASE_NOTES_2.3.1.md:5` | `2.2.5`, `2.3.0` |
| `docs/RELEASE_NOTES_2.3.2.md:2` | `2.3.2` |
| `docs/RELEASE_NOTES_2.3.5.md:2` | `2.3.5` |
| `docs/RELEASE_NOTES_2.3.5.md:4` | `2.3.2` |
| `docs/RELEASE_NOTES_2.3.5.md:8` | `2.3.5` |
| `docs/USER_GUIDE.md:2` | `2.3.5` |
| `docs/USER_GUIDE.md:35` | `2.3.5` |
| `docs/USER_GUIDE.md:48` | `2.3.5` |
| `docs/VERSION_1_5_0.md:1` | `1.5.0` |
| `docs/VERSION_1_5_0.md:3` | `1.5.0` |
| `docs/history/INSTALL_VERSION_2.0.1.txt:1` | `2.0.1` |
| `docs/history/INSTALL_VERSION_2.0.1.txt:4` | `2.0.0` |
| `docs/history/INSTALL_VERSION_2.0.1.txt:13` | `2.0.1` |
| `docs/history/INSTALL_VERSION_2.0.txt:1` | `2.0.0` |
| `pyproject.toml:4` | `2.3.5` |
| `tests/test_build_info.py:28` | `2.0.2` |
| `tests/test_build_info.py:29` | `2.1.0` |
| `tests/test_config.py:14` | `0.0.1` |
| `tests/test_release_version.py:18` | `2.3.5` |
| `tests/test_release_version.py:30` | `1.2.3`, `9.8.7` |
| `tests/test_release_version.py:31` | `1.2.3`, `9.8.7` |
| `tests/test_release_version.py:33` | `1.2.3`, `9.8.7` |
| `tests/test_release_version.py:34` | `1.2.3` |
| `tests/test_release_version.py:38` | `2.2.5` |
| `tests/test_release_version.py:40` | `2.2.5` |
| `tests/test_release_version.py:43` | `1.2.0` |
| `tests/test_release_version.py:44` | `1.0.0` |
| `tests/test_release_version.py:45` | `2.3.0` |
| `tests/test_release_version.py:48` | `2.3.0` |
| `tests/test_release_version.py:50` | `1.2.0` |
| `tests/test_release_version.py:51` | `1.0.0` |
| `tests/test_release_version.py:65` | `2.2.5` |
| `tests/test_release_version.py:66` | `2.0.0` |
