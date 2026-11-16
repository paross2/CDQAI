<!-- CDQAI file version: 2.5.0 -->
# CDQAI – Crash Data Quality Artificial Intelligence

This file is a design outline, not a completed specification. The current
implementation combines deterministic rules, structured anomaly scoring,
narrative embeddings, evidence collection, finding synthesis, and local reports.
The Evidence object is the shared contract between analysis and reporting.

The intended scope is crash/roadway, vehicle, and person data supplied through
locally configured sources. Current loaders support a crash source and a
narrative source; separate vehicle/person validation remains future work.
Findings are review leads, not proof of errors. Protected inputs and outputs
must stay in approved environments.

See TECHNICAL_ARCHITECTURE.md for the implemented pipeline, DEVELOPMENT_REVIEW.md
for known limitations, and ROADMAP.md for the next work. A fuller specification of record relationships, validation criteria, and analyst evaluation remains to
be written and reviewed with the project owner.
