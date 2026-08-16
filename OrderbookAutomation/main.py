from __future__ import annotations

import logging
import sys

from config import AppConfig, get_default_config
from modules.derived_dataset_manager import run_phase2
from modules.dictionary_builder import build_data_dictionary_markdown
from modules.loader import load_workbooks
from modules.master_builder import build_master_workbook
from modules.phase4_manager import run_phase4
from modules.profiler import build_workbook_profiles, write_workbook_profile
from modules.source_discovery import SourceDiscoveryError
from modules.utils import Timer, ensure_directory, setup_logging
from modules.validator import DataValidationError, validate_loaded_workbooks
from modules.workbook_manager import build_join_key_analysis_markdown, discover_join_key_candidates


def _first_sheet_dataframe(loaded_workbooks, workbook_key: str):
    """Return the first worksheet dataframe for a loaded workbook key, or None."""
    workbook_data = loaded_workbooks.get(workbook_key)
    if workbook_data is None or not workbook_data.worksheets:
        return None
    return next(iter(workbook_data.worksheets.values())).dataframe


def run_phase1() -> "AppConfig":
    """Run the full pipeline: Phase 1 ingestion, Phase 2 derived datasets, Phase 3 business master.

    Returns the resolved ``AppConfig`` so the entry point can report the
    output folder location and log file path to the business user without
    re-deriving them.
    """
    config = get_default_config()

    ensure_directory(config.output_dir)
    ensure_directory(config.logs_dir)
    ensure_directory(config.docs_dir)

    logger = setup_logging(config.logs_dir, log_name="phase1.log")

    with Timer() as timer:
        logger.info("Starting Phase 1 ingestion workflow")
        logger.info("Application root=%s | input_dir=%s", config.project_root, config.input_dir)

        loaded_workbooks = load_workbooks(config, logger)
        validation_result = validate_loaded_workbooks(config, loaded_workbooks, logger)

        summary_df, columns_df = build_workbook_profiles(loaded_workbooks, logger)
        profile_path = config.output_dir / "Workbook_Profile.xlsx"
        write_workbook_profile(summary_df, columns_df, profile_path, logger)

        dictionary_markdown = build_data_dictionary_markdown(loaded_workbooks, config.join_key_hints)
        dictionary_path = config.docs_dir / "DATA_DICTIONARY.md"
        dictionary_path.write_text(dictionary_markdown, encoding="utf-8")
        logger.info("Wrote data dictionary to %s", dictionary_path)

        key_candidates = discover_join_key_candidates(loaded_workbooks, config.join_key_hints, logger)
        join_key_markdown = build_join_key_analysis_markdown(key_candidates)
        join_key_path = config.docs_dir / "JOIN_KEY_ANALYSIS.md"
        join_key_path.write_text(join_key_markdown, encoding="utf-8")
        logger.info("Wrote join key analysis to %s", join_key_path)

        if validation_result.has_errors:
            raise DataValidationError("Phase 1 validation failed. Review logs/phase1.log for details.")

        phase2_result = run_phase2(loaded_workbooks, config, logger, timer.elapsed_seconds)
        logger.info("Phase 2 completed successfully. Derived workbook saved to %s", phase2_result.output_path)

        master_df = run_phase3(loaded_workbooks, config, logger)

        if master_df is not None:
            phase4_result = run_phase4(
                loaded_workbooks,
                master_df,
                phase2_result.ups_inventory_df,
                phase2_result.moq_validation_df,
                config,
                logger,
            )
            logger.info(
                "Phase 4 completed successfully. Sales Summary saved to %s | POB saved to %s",
                phase4_result.sales_summary_path,
                phase4_result.pob_path,
            )
        else:
            logger.warning("Skipping Phase 4: Phase 3 Business Master dataset was not produced")

        logger.info("Phase 1 completed successfully in %.2f seconds", timer.elapsed_seconds)

    return config


def run_phase3(loaded_workbooks, config, logger):
    """Run Phase 3: build the Business Master Dataset from the canonical orderbook source.

    Reuses the existing ``modules.master_builder.build_master_workbook``
    implementation without altering its merge/business logic. This function
    only wires Phase 1-loaded dataframes into that existing function and
    writes the output workbook under ``config.output_dir``. Returns the
    resulting master dataframe so Phase 4 can build on it directly.
    """
    orderbook_df = _first_sheet_dataframe(loaded_workbooks, "orderbook")
    if orderbook_df is None:
        logger.warning("Skipping Phase 3: canonical orderbook source was not loaded")
        return None

    source_frames = {
        "moq": _first_sheet_dataframe(loaded_workbooks, "moq"),
        "inventory": _first_sheet_dataframe(loaded_workbooks, "inventory"),
        "open_orders": _first_sheet_dataframe(loaded_workbooks, "open_order_summary"),
        "sales_summary": _first_sheet_dataframe(loaded_workbooks, "sales_summary"),
        "sales_trend": _first_sheet_dataframe(loaded_workbooks, "sales_trend"),
        "buying_groups": _first_sheet_dataframe(loaded_workbooks, "buying_groups"),
        "awards": _first_sheet_dataframe(loaded_workbooks, "awards"),
        "critical_inventory_tracker": _first_sheet_dataframe(loaded_workbooks, "critical_inventory_tracker"),
    }
    source_frames = {key: value for key, value in source_frames.items() if value is not None}

    output_path = config.output_dir / "Business_Master_Data.xlsx"
    result = build_master_workbook(orderbook_df, source_frames, output_path, logger=logger)
    logger.info("Phase 3 completed successfully. Business Master workbook saved to %s", output_path)
    return result.master_df


def main() -> int:
    """Entry point with business-friendly error handling.

    Known, expected failure modes (missing/ambiguous input files, validation
    failures) are shown to the business user as short, actionable messages.
    Full technical details (including tracebacks) are always written to the
    log file so support staff can diagnose issues.
    """
    try:
        config = run_phase1()
    except SourceDiscoveryError as exc:
        print(f"\nERROR: {exc}\n")
        return 1
    except DataValidationError as exc:
        print(f"\nERROR: {exc}\nReview the log file in the 'logs' folder for details.\n")
        return 1
    except Exception as exc:  # noqa: BLE001 - top-level safety net for business users
        # Use the SAME logger instance configured in setup_logging() (name
        # "orderbook_automation_phase1"), not a module-level logger, so the
        # full traceback is guaranteed to reach logs/phase1.log rather than
        # being silently dropped (the root logger has no file handler).
        logging.getLogger("orderbook_automation_phase1").exception(
            "Unhandled exception during pipeline execution"
        )
        print(f"\nAn unexpected error occurred: {exc}\nReview the log file in the 'logs' folder for details.\n")
        return 1

    print("\nOrderbook processing completed successfully.")
    print(f"Output folder:\n{config.output_dir}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

