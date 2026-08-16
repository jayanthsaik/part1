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


@dataclass(frozen=True)
class Phase2Result:
    """All derived Phase 2 outputs."""

    ups_inventory_df: pd.DataFrame
    lookup_keys_df: pd.DataFrame
    moq_validation_df: pd.DataFrame
    statistics_df: pd.DataFrame
    output_path: Path


def run_phase2(loaded_workbooks: dict[str, WorkbookData], config: AppConfig, logger, execution_time_seconds: float) -> Phase2Result:
    """Generate all Phase 2 derived datasets from Phase 1 loaded workbooks."""
    inventory_df = _get_sheet_dataframe(loaded_workbooks, "inventory")
    open_orders_df = _get_sheet_dataframe(loaded_workbooks, "open_order_summary")
    sales_summary_df = _get_sheet_dataframe(loaded_workbooks, "sales_summary")

    inventory_result = build_ups_inventory(inventory_df, open_orders_df, config.phase2, logger)
    lookup_result = build_lookup_keys(sales_summary_df, logger)
    moq_result = build_moq_validation(sales_summary_df, logger)
    statistics_df = _build_statistics(inventory_result, lookup_result, moq_result, execution_time_seconds)

    output_path = config.output_dir / config.phase2.derived_workbook_name
    _write_derived_workbook(
        inventory_result.dataframe,
        lookup_result.dataframe,
        moq_result.dataframe,
        statistics_df,
        output_path,
    )
    logger.info("Wrote Phase 2 derived workbook to %s", output_path)

    return Phase2Result(
        ups_inventory_df=inventory_result.dataframe,
        lookup_keys_df=lookup_result.dataframe,
        moq_validation_df=moq_result.dataframe,
        statistics_df=statistics_df,
        output_path=output_path,
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