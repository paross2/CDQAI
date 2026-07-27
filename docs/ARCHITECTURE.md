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

Transforms evidence into analyst-facing findings.

## Explain

Creates deterministic explanations from evidence.

## LLM

Optional local reviewer for analyst-friendly summaries. The LLM explains; it does not decide.

## Reports

Writes CSV, JSON, and future dashboard artifacts.
