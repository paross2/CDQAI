# CDQAI 2.2.2 — Transparent Narrative Evidence

Version 2.2.2 is a usability, transparency, and reproducibility release. It does not alter the core anomaly thresholds or priority formula.

## Changes

- Adds the complete crash narrative to each expanded dashboard finding.
- Highlights narrative phrases used by deterministic narrative-injury conflict rules.
- Clearly labels embedding-only narrative anomalies as whole-document statistical signals; it does not falsely claim that individual words caused an embedding score.
- Adds reliable Git branch, commit, tag, dirty-tree, and repository provenance. Environment-variable fallbacks are supported for source archives and packaged deployments.
- Reports Windows 11 correctly by reading Windows registry build information rather than relying solely on Python's Windows 10 compatibility string.
- Expands dependency reporting to include `huggingface-hub`, `transformers`, `torch`, and `tokenizers`.
- Adds explicit AI Models Used and System Provenance sections, including runtime timestamp, architecture, GPU availability, and random seed.
- Adds tests for metadata fallbacks, Windows build interpretation, narrative rendering, safe highlighting, and AI-stack disclosure.

## Attribution limitation

Sentence Transformers produces an embedding for the narrative as a whole. Version 2.2.2 only highlights phrases when a deterministic rule explicitly used them. Embedding-only findings display the narrative but do not assign causal importance to individual words or sentences.
