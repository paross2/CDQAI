# CDQAI 2.1.1 — Build Metadata & Provenance

Version 2.1.1 adds centralized project metadata, software provenance, authorship and contributor credit, AI-assistance disclosure, funding acknowledgment, licensing, citation metadata, and runtime environment reporting. It does not change the anomaly-detection algorithms or scoring behavior introduced in Version 2.1.0.

## Added

- Central metadata source in `cdqai/core/build_info.py`.
- Runtime Python, operating-system, Git, and dependency-version reporting.
- `AUTHORS.md`, `LICENSE`, `LICENSE-DOCS`, and `CITATION.cff`.
- Dashboard provenance, funding, attribution, licensing, and disclaimer content.
- Regression tests for metadata consistency and stale current-version references.

## Authorship

- Lead Developer: Paul Ross, Research Scientist Principal, Kentucky Transportation Center.
- Contributing Developer: Nathaniel Swallom, Research Scientist, Kentucky Transportation Center.
- AI Engineering Assistant: OpenAI ChatGPT.

## Funding

Supported through Federal Traffic Safety Information Systems (Section 405(c)) grant funding administered by the Kentucky Office of Highway Safety under the Kentucky Transportation Cabinet.
