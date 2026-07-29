from __future__ import annotations

import argparse
import sys
import time

from cdqai.core.config import load_config
from cdqai.core.logger import setup_logger
from cdqai.core.manifest import write_run_manifest
from cdqai.core.timing import timed_step
from cdqai.data.cache import load_dataframe_cache, write_dataframe_cache
from cdqai.data.database import DatabaseManager
from cdqai.data.preprocessing import build_dataset, build_dataset_from_merged_cache
from cdqai.reports.dataset_report import write_dataset_outputs
from cdqai.reports.evidence_report import write_evidence_outputs
from cdqai.rules.engine import RuleEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cdqai",
        description="Crash Data Quality Artificial Intelligence command line interface.",
    )
    parser.add_argument("--health-check", action="store_true", help="Run a basic project health check.")
    parser.add_argument("--load-data", action="store_true", help="Load, merge, summarize, and cache crash/narrative data.")
    parser.add_argument("--run-models", action="store_true", help="Run structured and narrative model scoring.")
    parser.add_argument("--run-rules", action="store_true", help="Run the Kentucky deterministic rule engine.")
    parser.add_argument("--run-all", action="store_true", help="Run the unified Version 2.1.1 evidence, finding, and dashboard pipeline.")
    parser.add_argument("--refresh-cache", action="store_true", help="Ignore existing cache and rebuild SQL/embedding caches.")
    return parser


def log_banner(logger, config, subtitle: str | None = None) -> None:
    logger.info("===================================================")
    logger.info("%s (%s)", config.project_name, config.short_name)
    logger.info("Version: %s", config.version)
    logger.info("Milestone: %s", config.milestone)
    if subtitle:
        logger.info("%s", subtitle)
    logger.info("Project root: %s", config.project_root)
    logger.info("===================================================")


def run_health_check() -> int:
    config = load_config()
    logger = setup_logger(config.logs_dir, config.log_level)

    log_banner(logger, config)

    logger.info("Cache directory: %s", config.cache_dir)
    logger.info("Logs directory: %s", config.logs_dir)
    logger.info("Outputs directory: %s", config.outputs_dir)
    logger.info("Rules directory: %s", config.rules_dir)
    logger.info("CDQAI health check completed successfully.")
    return 0


def load_dataset(config, logger, refresh_cache: bool = False):
    cached_merged = None

    if config.use_cache and not refresh_cache:
        with timed_step(logger, "Checking merged dataframe cache"):
            cached_merged = load_dataframe_cache(config.merged_cache_path, logger)

    if cached_merged is not None:
        with timed_step(logger, "Building dataset from merged cache"):
            return build_dataset_from_merged_cache(cached_merged, config, logger)

    with timed_step(logger, "Connecting to SQL Server"):
        db = DatabaseManager(config=config, logger=logger)
        db.test_connection()

    with timed_step(logger, "Loading crash records"):
        crashes = db.load_crashes()

    with timed_step(logger, "Loading narrative records"):
        narratives = db.load_narratives()

    with timed_step(logger, "Building merged CrashDataset"):
        dataset = build_dataset(crashes, narratives, config, logger)

    if config.write_cache:
        with timed_step(logger, "Writing merged dataframe cache"):
            write_dataframe_cache(dataset.merged, config.merged_cache_path, logger)

    return dataset


def run_data_pipeline(refresh_cache: bool = False) -> int:
    start = time.perf_counter()
    config = load_config()
    logger = setup_logger(config.logs_dir, config.log_level)

    log_banner(logger, config, "Data pipeline starting.")

    try:
        dataset = load_dataset(config, logger, refresh_cache=refresh_cache)

        with timed_step(logger, "Writing dataset outputs"):
            write_dataset_outputs(dataset, config, logger)

        elapsed = time.perf_counter() - start
        manifest_path = write_run_manifest(config, elapsed, dataset.metadata)
        logger.info("Run manifest written: %s", manifest_path)
        logger.info("CDQAI data pipeline completed successfully.")
        return 0

    except Exception:
        logger.exception("CDQAI data pipeline failed.")
        return 1


def run_models(refresh_cache: bool = False) -> int:
    # Lazy imports keep health-check and rule-only workflows from requiring optional ML packages.
    from cdqai.detectors.model_runner import run_model_scoring
    from cdqai.reports.model_report import write_model_outputs

    start = time.perf_counter()
    config = load_config()
    logger = setup_logger(config.logs_dir, config.log_level)

    log_banner(logger, config, "Model scoring pipeline starting.")

    try:
        dataset = load_dataset(config, logger, refresh_cache=refresh_cache)

        with timed_step(logger, "Writing dataset outputs"):
            write_dataset_outputs(dataset, config, logger)

        with timed_step(logger, "Running model scoring"):
            scores, model_metadata = run_model_scoring(
                dataset,
                config,
                logger,
                refresh_cache=refresh_cache,
            )

        with timed_step(logger, "Writing model outputs"):
            write_model_outputs(dataset, scores, config, logger)

        elapsed = time.perf_counter() - start
        manifest_path = write_run_manifest(config, elapsed, dataset.metadata, model_metadata=model_metadata)
        logger.info("Run manifest written: %s", manifest_path)
        logger.info("CDQAI model scoring completed successfully.")
        return 0

    except Exception:
        logger.exception("CDQAI model scoring failed.")
        return 1


def run_rules(refresh_cache: bool = False) -> int:
    start = time.perf_counter()
    config = load_config()
    logger = setup_logger(config.logs_dir, config.log_level)

    log_banner(logger, config, "Kentucky Rule Engine starting.")

    try:
        dataset = load_dataset(config, logger, refresh_cache=refresh_cache)

        with timed_step(logger, "Writing dataset outputs"):
            write_dataset_outputs(dataset, config, logger)

        with timed_step(logger, "Running Kentucky Rule Engine"):
            evidence = RuleEngine(config=config, logger=logger).run(dataset)

        with timed_step(logger, "Writing evidence outputs"):
            write_evidence_outputs(evidence, config, logger)

        elapsed = time.perf_counter() - start
        rule_metadata = {
            "evidence_count": len(evidence.items),
            "evidence_records": len(evidence.by_mfn()),
        }
        manifest_path = write_run_manifest(
            config,
            elapsed,
            dataset.metadata,
            model_metadata={"rules": rule_metadata},
        )
        logger.info("Run manifest written: %s", manifest_path)
        logger.info("CDQAI Kentucky Rule Engine completed successfully.")
        return 0

    except Exception:
        logger.exception("CDQAI Kentucky Rule Engine failed.")
        return 1



def run_all(refresh_cache: bool = False) -> int:
    from cdqai.detectors.model_runner import run_model_scoring
    from cdqai.evidence.engine import EvidenceCollection
    from cdqai.evidence.model_evidence import build_model_evidence
    from cdqai.findings.engine import FindingEngine
    from cdqai.reports.dashboard_report import write_dashboard
    from cdqai.reports.finding_report import write_finding_outputs
    from cdqai.reports.model_report import write_model_outputs

    start = time.perf_counter()
    config = load_config()
    logger = setup_logger(config.logs_dir, config.log_level)
    log_banner(logger, config, "Unified evidence pipeline starting.")
    try:
        dataset = load_dataset(config, logger, refresh_cache=refresh_cache)
        with timed_step(logger, "Writing dataset outputs"):
            write_dataset_outputs(dataset, config, logger)
        with timed_step(logger, "Running deterministic rules"):
            rule_evidence = RuleEngine(config=config, logger=logger).run(dataset)
        with timed_step(logger, "Running model scoring"):
            scores, model_metadata = run_model_scoring(dataset, config, logger, refresh_cache=refresh_cache)
        with timed_step(logger, "Writing model outputs"):
            write_model_outputs(dataset, scores, config, logger)
        with timed_step(logger, "Converting model scores to evidence"):
            model_evidence = build_model_evidence(scores, config)
        evidence = EvidenceCollection(items=[*rule_evidence.items, *model_evidence.items])
        with timed_step(logger, "Writing unified evidence outputs"):
            write_evidence_outputs(evidence, config, logger)
        with timed_step(logger, "Synthesizing analyst findings"):
            findings = FindingEngine().run(evidence)
            write_finding_outputs(findings, dataset, config, logger)
        with timed_step(logger, "Writing dashboard"):
            write_dashboard(dataset, evidence, findings, config, logger)
        elapsed = time.perf_counter() - start
        metadata = dict(model_metadata)
        metadata.update({"rule_evidence": len(rule_evidence.items), "model_evidence": len(model_evidence.items), "findings": len(findings)})
        write_run_manifest(config, elapsed, dataset.metadata, model_metadata=metadata)
        logger.info("CDQAI unified evidence pipeline completed successfully.")
        return 0
    except Exception:
        logger.exception("CDQAI unified evidence pipeline failed.")
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.run_all:
        return run_all(refresh_cache=args.refresh_cache)

    if args.run_rules:
        return run_rules(refresh_cache=args.refresh_cache)

    if args.run_models:
        return run_models(refresh_cache=args.refresh_cache)

    if args.load_data:
        return run_data_pipeline(refresh_cache=args.refresh_cache)

    return run_health_check()


if __name__ == "__main__":
    sys.exit(main())
