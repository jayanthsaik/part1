"""OrderbookAutomation - application entry point.

PRODUCTION BEHAVIOUR
--------------------
A normal (DEBUG_MODE=False) run produces exactly ONE business artifact:

    <application root>/output/POB.xlsx

Every intermediate dataset (Phase 2 derived data, the Phase 3 Business
Master, historical sales, enrichment and validation frames) is carried
between phases IN MEMORY. The diagnostic workbooks/markdown documents are
still fully implemented and are written only when DEBUG_MODE is enabled
(see config.is_debug_mode / the ORDERBOOK_DEBUG environment variable).

Enabling DEBUG_MODE changes OUTPUT ONLY. Every business calculation,
merge, lookup, threshold and formatting rule is identical in both modes.
"""

from __future__ import annotations

import logging
import sys

from config import (
    APPLICATION_GENERATED_DOC_FILES,
    APPLICATION_GENERATED_OUTPUT_FILES,
    PRODUCTION_OUTPUT_FILENAME,
    AppConfig,
    get_default_config,
)
from modules.derived_dataset_manager import run_phase2
from modules.dictionary_builder import build_data_dictionary_markdown
from modules.loader import load_workbooks
from modules.master_builder import build_master_workbook
from modules.phase4_manager import run_phase4
from modules.profiler import build_workbook_profiles, write_workbook_profile
from modules.source_discovery import SourceDiscoveryError
from modules.utils import Timer, clean_generated_outputs, ensure_directory, setup_logging
from modules.validator import DataValidationError, validate_loaded_workbooks
from modules.workbook_manager import build_join_key_analysis_markdown, discover_join_key_candidates


def _first_sheet_dataframe(loaded_workbooks, workbook_key: str):
    """Return the first worksheet dataframe for a loaded workbook key, or None."""
    workbook_data = loaded_workbooks.get(workbook_key)
    if workbook_data is None or not workbook_data.worksheets:
        return None
    return next(iter(workbook_data.worksheets.values())).dataframe


def prepare_environment() -> "AppConfig":
    """Resolve application paths and ensure the standard folders exist.

    All directories are resolved relative to the application root (the folder
    containing the .exe when frozen), never the current working directory and
    never a developer-specific absolute path.
    """
    config = get_default_config()

    ensure_directory(config.input_dir)
    ensure_directory(config.output_dir)
    ensure_directory(config.logs_dir)
    if config.debug_mode:
        ensure_directory(config.docs_dir)

    return config


def run_pipeline(config: "AppConfig", logger) -> "AppConfig":
    """Run Phases 1-4 and write the single production workbook (POB.xlsx)."""
    with Timer() as timer:
        logger.info("Starting Orderbook automation workflow")
        logger.info(
            "Application root=%s | input_dir=%s | output_dir=%s | debug_mode=%s",
            config.project_root,
            config.input_dir,
            config.output_dir,
            config.debug_mode,
        )

        # ---- Phase 1: dynamic discovery, load, validate ----
        loaded_workbooks = load_workbooks(config, logger)
        validation_result = validate_loaded_workbooks(config, loaded_workbooks, logger)

        # Profiling/documentation are DEBUG-ONLY artifacts. Only serialization
        # is conditional; no business calculation depends on them.
        if config.debug_mode:
            summary_df, columns_df = build_workbook_profiles(loaded_workbooks, logger)
            write_workbook_profile(summary_df, columns_df, config.output_dir / "Workbook_Profile.xlsx", logger)

            dictionary_path = config.docs_dir / "DATA_DICTIONARY.md"
            dictionary_path.write_text(
                build_data_dictionary_markdown(loaded_workbooks, config.join_key_hints),
                encoding="utf-8",
            )
            logger.info("[DEBUG] Wrote data dictionary to %s", dictionary_path)

            key_candidates = discover_join_key_candidates(loaded_workbooks, config.join_key_hints, logger)
            join_key_path = config.docs_dir / "JOIN_KEY_ANALYSIS.md"
            join_key_path.write_text(build_join_key_analysis_markdown(key_candidates), encoding="utf-8")
            logger.info("[DEBUG] Wrote join key analysis to %s", join_key_path)

        if validation_result.has_errors:
            raise DataValidationError(
                "Input validation failed. Review the log file in the 'logs' folder for details."
            )

        # ---- Phase 2: derived datasets (in memory) ----
        phase2_result = run_phase2(loaded_workbooks, config, logger, timer.elapsed_seconds)
        logger.info("Phase 2 completed successfully")

        # ---- Phase 3: Business Master (in memory) ----
        master_df = run_phase3(loaded_workbooks, config, logger)
        if master_df is None:
            raise DataValidationError(
                "The Business Master dataset could not be produced because the Orderbook source was not found."
            )

        # ---- Phase 4: final POB.xlsx ----
        phase4_result = run_phase4(
            loaded_workbooks,
            master_df,
            phase2_result.ups_inventory_df,
            phase2_result.moq_validation_df,
            config,
            logger,
        )
        logger.info("Phase 4 completed successfully. POB saved to %s", phase4_result.pob_path)
        logger.info("Workflow completed successfully in %.2f seconds", timer.elapsed_seconds)

    return config


def run_phase3(loaded_workbooks, config, logger):
    """Run Phase 3: build the Business Master Dataset from the canonical orderbook source.

    Reuses the existing ``modules.master_builder.build_master_workbook``
    implementation without altering its merge/business logic. In production the
    resulting master dataframe is returned purely in memory for Phase 4; the
    Business_Master_Data.xlsx validation workbook is written only in DEBUG mode.
    """
    orderbook_df = _first_sheet_dataframe(loaded_workbooks, "orderbook")
    if orderbook_df is None:
        logger.warning("Skipping Phase 3: canonical orderbook source was not loaded")
        return None

    source_frames = {
        "moq": _first_sheet_dataframe(loaded_workbooks, "moq"),
        "inventory": _first_sheet_dataframe(loaded_workbooks, "inventory"),
        "open_orders": _first_sheet_dataframe(loaded_workbooks, "open_order_summary"),
        "sales_trend": _first_sheet_dataframe(loaded_workbooks, "sales_trend"),
        "buying_groups": _first_sheet_dataframe(loaded_workbooks, "buying_groups"),
        "awards": _first_sheet_dataframe(loaded_workbooks, "awards"),
        "critical_inventory_tracker": _first_sheet_dataframe(loaded_workbooks, "critical_inventory_tracker"),
        "upload_sheet": _first_sheet_dataframe(loaded_workbooks, "upload_sheet"),
    }
    source_frames = {key: value for key, value in source_frames.items() if value is not None}

    # DEBUG-ONLY diagnostic workbook; None keeps the master dataset in memory.
    output_path = config.output_dir / "Business_Master_Data.xlsx" if config.debug_mode else None
    result = build_master_workbook(orderbook_df, source_frames, output_path, logger=logger)
    logger.info("Phase 3 completed successfully")
    return result.master_df


def main() -> int:
    """Entry point with business-friendly error handling.

    Known, expected failure modes (missing/ambiguous input files, validation
    failures) are shown to the business user as short, actionable messages.
    Full technical details (including tracebacks) are always written to the
    log file in logs/ so support staff can diagnose issues.

    Returns 0 on success and a non-zero exit code on any failure.
    """
    config = None
    logger = None
    try:
        config = prepare_environment()
        logger = setup_logging(config.logs_dir, log_name="orderbook_automation.log")

        # Remove stale application-generated outputs from a previous run so a
        # failed run can never leave the previous POB.xlsx looking current.
        # ONLY this application's own known filenames are eligible for removal.
        clean_generated_outputs(config.output_dir, APPLICATION_GENERATED_OUTPUT_FILES, logger)
        if config.debug_mode:
            clean_generated_outputs(config.docs_dir, APPLICATION_GENERATED_DOC_FILES, logger)

        run_pipeline(config, logger)

    except SourceDiscoveryError as exc:
        if logger is not None:
            logger.error("Input discovery failed: %s", exc)
        print(f"\nProcessing failed.\n\n{exc}\n\nCheck the 'logs' folder for details.\n")
        return 1
    except DataValidationError as exc:
        if logger is not None:
            logger.error("Validation failed: %s", exc)
        print(f"\nProcessing failed.\n\n{exc}\n\nCheck the 'logs' folder for details.\n")
        return 1
    except Exception as exc:  # noqa: BLE001 - top-level safety net for business users
        # Use the SAME logger instance configured in setup_logging() so the
        # full traceback is guaranteed to reach the log file rather than being
        # silently dropped (the root logger has no file handler).
        logging.getLogger("orderbook_automation_phase1").exception(
            "Unhandled exception during pipeline execution"
        )
        print(f"\nProcessing failed.\n\n{exc}\n\nCheck the 'logs' folder for details.\n")
        return 1

    output_file = config.output_dir / PRODUCTION_OUTPUT_FILENAME
    print("\nOrderbook processing completed successfully.")
    print(f"\nOutput:\n{output_file}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
