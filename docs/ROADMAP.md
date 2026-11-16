<!-- CDQAI file version: 2.5.1 -->
# CDQAI Roadmap

## Current baseline

The current application includes configured source/cache loading, deterministic crash-data rules,
structured and narrative models, evidence collection, finding synthesis, local
reports, and an interactive dashboard. The synthetic smoke run and user guide
support local setup. See VERSION for the current release.

Version 2.4.0 added an optional local e-scooter narrative classifier. It is
disabled by default, relies on private user-supplied labels and configured
vehicle-record sources, and does not change crash coding. The scooter code is
configurable and must be confirmed against the applicable codebook.

Version 2.5.0 adds optional coded-factor filters and record details for Human,
Environmental, and Vehicle factors. It projects only configured identifiers,
years, and factor codes from local sources. Factor-specific narrative predictions are not
implemented; the dashboard states this limitation explicitly. The separate
scooter MFN-only PDF control has been removed.

## Next work, after local analyst review

Future research will evaluate whether narratives reveal uncoded factors,
including human factors such as possible distracted driving, beyond structured
fields. That capability is not implemented or enabled; each category-specific
model will require supervised training, negation/context handling, supporting
excerpts, and analyst validation. Do not present synthetic examples or
candidate vocabulary as production training data.

1. Make MFN normalization and duplicate handling consistent across joins and reports.
2. Validate embedding caches against narrative content and model identity.
3. Validate the corrected base-signal agreement and provisional severity weights.
4. Improve specific explanations, recommended actions, and crash-year fallback.
5. Measure embedding runtime and memory at the intended dataset scale.
6. Use analyst dispositions to evaluate thresholds and scoring weights.

Separate vehicle/person relationships and validation remain part of the intended
scope. Optional local LLM assistance is implemented; broader narrative fact extraction requires
separate design and validation. No new feature version is assigned until its
scope is agreed. Historical release notes preserve earlier milestone descriptions.

See DEVELOPMENT_REVIEW.md for the evidence behind these priorities. Real-data
runs and output review are performed privately by authorized users.
