<!-- CDQAI file version: 2.2.5 -->
# CDQAI Roadmap

## Current baseline

The current application includes SQL/cache loading, deterministic Rec01 rules,
structured and narrative models, evidence collection, finding synthesis, local
reports, and an interactive dashboard. The synthetic smoke run and user guide
support local setup. See VERSION for the current release.

## Next work, after local analyst review

1. Make MFN normalization and duplicate handling consistent across joins and reports.
2. Validate embedding caches against narrative content and model identity.
3. Correct derived-signal double counting in evidence strength and priority.
4. Improve specific explanations, recommended actions, and crash-year fallback.
5. Measure embedding runtime and memory at the intended dataset scale.
6. Use analyst dispositions to evaluate thresholds and scoring weights.

Separate Rec02/Rec03 relationships and validation remain part of the intended
scope. Broader narrative fact extraction and any local LLM assistance require
separate design and validation. No new feature version is assigned until its
scope is agreed. Historical release notes preserve earlier milestone descriptions.

See DEVELOPMENT_REVIEW.md for the evidence behind these priorities. Real-data
runs and output review are performed privately by authorized users.
