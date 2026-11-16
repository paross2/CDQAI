# CDQAI Version 1.5.0 — Kentucky Rule Engine

Version 1.5.0 introduces the first deterministic Kentucky rule engine.

## Purpose

The Rule Engine converts known Kentucky traffic records quality checks into structured evidence. This moves CDQAI beyond model scores and toward analyst-reviewable findings.

## Added

- `BaseRule`
- `RuleResult`
- `RuleEngine`
- Missing narrative rule
- Sparse narrative rule
- Required-field completeness rule
- Narrative injury conflict rule
- `--run-rules` CLI command
- Evidence CSV output
- Evidence summary output

## Design Principle

Rules do not directly create final classifications. Rules create evidence.

Future versions will convert evidence into findings, classifications, explanations, and analyst recommendations.

## Command

```powershell
.\.venv\Scripts\python.exe run_cdqai.py --run-rules
```

## Outputs

- `outputs/evidence.csv`
- `outputs/evidence_summary.csv`
- `outputs/run_manifest.json`
