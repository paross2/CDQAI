<!-- CDQAI file version: 2.2.5 -->
# CDQAI Architecture

CDQAI is organized around stable architectural layers rather than temporary sprint folders.

## Kentucky Layer

Defines the Kentucky-specific traffic records model:

- Rec01: Crash and Roadway
- Rec02: Vehicle
- Rec03: Driver

## Core

Shared utilities such as configuration, logging, path discovery, timing, and run manifests.

## Data

Database access, caching, preprocessing, and dataset objects.

## Models

Structured and narrative model scoring.

## Evidence

The central abstraction of CDQAI. Models, rules, and future detectors produce evidence. Classifiers, explanations, reports, and dashboards consume evidence.

## Rules

Deterministic Kentucky data quality checks.

## Classifiers

The `findings/` package transforms evidence into analyst-facing findings. The
separate `classifiers/` package is a reserved extension point.

## Explain

Deterministic explanations are currently assembled by the finding engine.
The separate `explain/` package is a reserved extension point.

## LLM

Reserved for a possible future local reviewer. No LLM currently determines
anomalies or generates the finding explanations.

## Reports

Writes CSV/JSON reports, the HTML dashboard, its narrative companion file, and
persisted narrative evidence. These are protected local runtime artifacts.
