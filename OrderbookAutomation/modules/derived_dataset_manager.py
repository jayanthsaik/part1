from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from config import AppConfig
from modules.derived_inventory import DerivedInventoryResult, build_ups_inventory
from modules.loader import WorkbookData
from modules.lookup_key_builder import LookupKeyResult, build_lookup_keys
from modules.moq_validator import MoqValidationResult, build_moq_validation
from modules.utils import normalize_ndc_key, coerce_numeric_column
from typing import Optional
import logging


@dataclass(frozen=True)
class Phase2Result:
    """All derived Phase 2 outputs."""

    ups_inventory_df: pd.DataFrame
    lookup_keys_df: pd.DataFrame
    moq_validation_df: pd.DataFrame
    statistics_df: pd.DataFrame
    output_path: Path
    upload_adjustments_df: Optional[pd.DataFrame] = None


def run_phase2(loaded_workbooks: dict[str, WorkbookData], config: AppConfig, logger, execution_time_seconds: float) -> Phase2Result:
    """Generate all Phase 2 derived datasets from Phase 1 loaded workbooks."""
    inventory_df = _get_sheet_dataframe(loaded_workbooks, "inventory")
    open_orders_df = _get_sheet_dataframe(loaded_workbooks, "open_order_summary")
    # optional upload-adjustments workbook (may be missing)
    # Resolved by header signature via the source registry -- never by filename.
    upload_df = _get_sheet_dataframe(loaded_workbooks, "upload_sheet")
    upload_adjustments_df = None
    if upload_df is None:
        logger.warning(
            "No Upload Sheet discovered in the input folder. UPS Inventory will be "
            "calculated WITHOUT upload adjustments (Upload_Qty = 0). If an upload "
            "sheet was provided, verify it contains the headers: "
            "NDC Code, Reason Code, Action, Sales Order Qty."
        )
    else:
        # permissive header discovery
        cols = {c.strip().lower(): c for c in upload_df.columns}
        ndc_col = cols.get("ndc") or cols.get("ndc code") or cols.get("ndc_code") or None
        reason_col = cols.get("reason code") or cols.get("reason_code") or None
        action_col = cols.get("action") or None
        qty_col = cols.get("sales order qty") or cols.get("sales_order_qty") or None

        if ndc_col is None:
            logger.warning("Upload adjustments sheet found but no NDC column located; ignoring upload adjustments")
        else:
            working = upload_df.copy()
            # normalize text
            working[ndc_col] = working[ndc_col].astype("string").str.strip().map(lambda v: normalize_ndc_key(v) if pd.notna(v) else v)

            # handle reason code (numeric or string)
            if reason_col is not None:
                reason_vals = working[reason_col].astype("string").str.strip().str.lower()
                reason_mask = reason_vals.isin({"1", "4"})
            else:
                reason_mask = pd.Series(True, index=working.index)

            # Action must be Y/Yes (case-insensitive)
            if action_col is not None:
                action_vals = working[action_col].astype("string").str.strip().str.lower()
                action_mask = action_vals.isin({"y", "yes"})
            else:
                action_mask = pd.Series(True, index=working.index)

            keep_mask = reason_mask & action_mask
            filtered = working.loc[keep_mask].copy()

            # Sales Order Qty may be missing column; default to 0 where absent
            if qty_col is None:
                filtered_qty = pd.Series(0, index=filtered.index)
            else:
                filtered_qty = coerce_numeric_column(filtered[qty_col]).fillna(0)

            filtered = filtered.assign(_upload_qty=filtered_qty)
            upload_adjustments_df = (
                filtered.groupby(ndc_col, dropna=False)["_upload_qty"]
                .sum()
                .rename("Upload_Qty")
                .reset_index()
                .rename(columns={ndc_col: "NDC"})
            )
            logger.info("Upload adjustments: %d rows aggregated into %d NDC groups", len(filtered), int(upload_adjustments_df["NDC"].nunique(dropna=True)))

    # Optional source -- this pipeline generates Sales Summary as an output
    # rather than requiring it as an input.
    sales_summary_df = _get_optional_sheet_dataframe(loaded_workbooks, "sales_summary")

    # BUSINESS RULE: upload adjustments are netted out of UPS Inventory
    # BEFORE the floor-to-zero step (see derived_inventory.build_ups_inventory).
    inventory_result = build_ups_inventory(
        inventory_df,
        open_orders_df,
        config.phase2,
        logger,
        upload_adjustments_df=upload_adjustments_df,
    )
    if sales_summary_df is not None:
        lookup_result = build_lookup_keys(sales_summary_df, logger)
        moq_result = build_moq_validation(sales_summary_df, logger)
    else:
        logger.warning(
            "Optional 'sales_summary' input not found; skipping Lookup Key and MOQ Validation derived datasets for this run."
        )
        lookup_result = LookupKeyResult(dataframe=pd.DataFrame(), total_rows=0, values_normalized=0, duplicate_lookup_keys=0)
        moq_result = MoqValidationResult(dataframe=pd.DataFrame(), failure_count=0)
    statistics_df = _build_statistics(inventory_result, lookup_result, moq_result, execution_time_seconds)

    output_path = config.output_dir / config.phase2.derived_workbook_name
    # DEBUG-ONLY ARTIFACT. Every derived dataset above is returned in memory
    # via Phase2Result and consumed directly by Phase 3/4, so skipping this
    # write cannot change any business value -- it is a pure diagnostic
    # side effect. In production only POB.xlsx is written.
    if getattr(config, "debug_mode", False):
        _write_derived_workbook(
            inventory_result.dataframe,
            lookup_result.dataframe,
            moq_result.dataframe,
            statistics_df,
            output_path,
        )
        logger.info("[DEBUG] Wrote Phase 2 derived workbook to %s", output_path)
    else:
        logger.info("Phase 2 derived datasets kept in memory (production mode; no intermediate workbook written)")

    return Phase2Result(
        ups_inventory_df=inventory_result.dataframe,
        lookup_keys_df=lookup_result.dataframe,
        moq_validation_df=moq_result.dataframe,
        statistics_df=statistics_df,
        output_path=output_path,
        upload_adjustments_df=upload_adjustments_df,
    )


def _get_sheet_dataframe(loaded_workbooks: dict[str, WorkbookData], workbook_key: str) -> pd.DataFrame:
    """Return a copy of the first worksheet dataframe for a loaded workbook key."""
    workbook_data = loaded_workbooks.get(workbook_key)
    if workbook_data is None:
        raise ValueError(f"Required workbook '{workbook_key}' not found in loaded workbook set")
    if not workbook_data.worksheets:
        raise ValueError(f"Workbook '{workbook_key}' does not contain any worksheets")
    first_sheet = next(iter(workbook_data.worksheets.values()))
    return first_sheet.dataframe.copy()


def _get_optional_sheet_dataframe(loaded_workbooks: dict[str, WorkbookData], workbook_key: str) -> pd.DataFrame | None:
    """Return a copy of the first worksheet dataframe for an optional workbook key, or None if absent.

    Unlike ``_get_sheet_dataframe``, this never raises when the workbook is
    missing -- used for logical sources marked ``mandatory=False`` in
    ``source_registry.py`` (e.g. "sales_summary", which this pipeline
    actually generates as an output rather than receiving as an input).
    """
    workbook_data = loaded_workbooks.get(workbook_key)
    if workbook_data is None or not workbook_data.worksheets:
        return None
    first_sheet = next(iter(workbook_data.worksheets.values()))
    return first_sheet.dataframe.copy()


def _build_statistics(
    inventory_result: DerivedInventoryResult,
    lookup_result: LookupKeyResult,
    moq_result: MoqValidationResult,
    execution_time_seconds: float,
) -> pd.DataFrame:
    """Build the required Phase 2 statistics sheet."""
    return pd.DataFrame(
        [
            {
                "Inventory Rows": inventory_result.inventory_rows,
                "Allocated Rows": inventory_result.allocated_rows,
                "Unique NDCs": inventory_result.unique_ndcs,
                "Missing Inventory": inventory_result.missing_inventory,
                "Missing Allocations": inventory_result.missing_allocations,
                "MOQ Failures": moq_result.failure_count,
                "Execution Time": round(execution_time_seconds, 2),
            }
        ]
    )


def _write_derived_workbook(
    ups_inventory_df: pd.DataFrame,
    lookup_keys_df: pd.DataFrame,
    moq_validation_df: pd.DataFrame,
    statistics_df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Write the Phase 2 derived datasets workbook with basic readability formatting."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        ups_inventory_df.to_excel(writer, sheet_name="UPS_Inventory", index=False)
        lookup_keys_df.to_excel(writer, sheet_name="Lookup_Keys", index=False)
        moq_validation_df.to_excel(writer, sheet_name="MOQ_Validation", index=False)
        statistics_df.to_excel(writer, sheet_name="Statistics", index=False)

    workbook = load_workbook(output_path)
    for worksheet in workbook.worksheets:
        _format_sheet(worksheet)
    workbook.save(output_path)


def _format_sheet(worksheet) -> None:
    """Apply basic workbook readability formatting to a worksheet."""
    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    for cell in worksheet[1]:
        cell.font = Font(bold=True)
    for column_cells in worksheet.columns:
        max_length = max((len(str(cell.value)) for cell in column_cells if cell.value is not None), default=0)
        worksheet.column_dimensions[get_column_letter(column_cells[0].column)].width = min(max(max_length + 2, 12), 55)