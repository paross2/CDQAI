# CDQAI Version 2.0.1 Release Notes

## Documentation and Transparency Update

Version 2.0.1 expands the explanation of CDQAI's implemented analytical workflow without changing the underlying Version 2.0 model and finding logic.

### Added

- Detailed dashboard explanations for every analytical stage.
- Rule-by-rule descriptions for missing narratives, sparse narratives, required fields, and narrative injury conflicts.
- Isolation Forest scoring explanation for structured variables.
- Semantic-embedding and Isolation Forest explanation for narratives.
- Config-driven display of model contamination, embedding model, ensemble weights, evidence thresholds, sparse-narrative length, and rule fields.
- Detailed deterministic finding-synthesis and priority-scoring explanation.
- Explicit disclosure that Version 2.0.1 does not use Llama or another LLM for synthesis.
- Regression tests ensuring dashboard threshold text follows active configuration values and does not falsely claim LLM synthesis.

### Known Issues Carried Forward

- `annual_findings.csv` may contain only its schema when no synthesized finding can be associated with a supported crash-year field.
- Dashboard count and findings integration remain under review for the Version 2.0.1 milestone.
- Anomaly thresholds will be evaluated against production analyst workload and review outcomes.
