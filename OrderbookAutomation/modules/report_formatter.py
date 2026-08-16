from __future__ import annotations

from pathlib import Path
from typing import Sequence

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.worksheet import Worksheet

# Documented SOP colors (Part E).
FILL_CONTROLLED_PRODUCT_PINK = PatternFill(start_color="FFC0CB", end_color="FFC0CB", fill_type="solid")
FILL_PRICE_ISSUE_ORANGE = PatternFill(start_color="FFA500", end_color="FFA500", fill_type="solid")
FILL_LOW_INVENTORY_YELLOW = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
FILL_CANCEL_RED = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
FILL_HOLD_BLUE = PatternFill(start_color="ADD8E6", end_color="ADD8E6", fill_type="solid")


def _sanitize_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``df`` with pandas NA/NaT/NaN and numpy scalar types replaced by
    plain Python values that openpyxl can write to a cell.

    openpyxl cannot serialize ``pd.NA`` (pandas' nullable-dtype missing marker) or numpy
    scalar types directly; converting to ``object`` dtype and replacing missing markers
    with ``None`` avoids "Cannot convert <NA> to Excel" errors while preserving actual
    business values (0 stays 0, empty string stays empty string, etc.).
    """
    safe_df = df.copy()
    for column in safe_df.columns:
        safe_df[column] = safe_df[column].astype(object).where(safe_df[column].notna(), None)
        safe_df[column] = safe_df[column].map(_to_excel_scalar)
    return safe_df


def _to_excel_scalar(value):
    if value is None or value is pd.NA:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if pd.api.types.is_scalar(value) and pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp,)):
        return value.to_pydatetime()
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, AttributeError):
            return value
    return value


def write_dataframe_sheet(
    workbook: Workbook,
    sheet_name: str,
    df: pd.DataFrame,
    *,
    freeze_header: bool = True,
    autofilter: bool = True,
) -> Worksheet:
    """Write ``df`` as values (never formulas) into a new worksheet with standard formatting."""
    worksheet = workbook.create_sheet(title=sheet_name)
    safe_df = _sanitize_for_excel(df)
    for row in dataframe_to_rows(safe_df, index=False, header=True):
        worksheet.append(row)

    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    if freeze_header:
        worksheet.freeze_panes = "A2"
    if autofilter and worksheet.max_row >= 1 and worksheet.max_column >= 1:
        worksheet.auto_filter.ref = worksheet.dimensions

    _autosize_columns(worksheet)
    return worksheet


def _autosize_columns(worksheet: Worksheet) -> None:
    for column_cells in worksheet.columns:
        max_length = max((len(str(cell.value)) for cell in column_cells if cell.value is not None), default=0)
        worksheet.column_dimensions[get_column_letter(column_cells[0].column)].width = min(max(max_length + 2, 10), 55)


def apply_business_rule_formatting(
    worksheet: Worksheet,
    df: pd.DataFrame,
    *,
    controlled_product_column: str = "Controlled_Product",
    price_issue_column: str = "Price_Issue",
    low_inventory_column: str = "Low_UPS_Inventory",
    price_columns: Sequence[str] = ("Unit Price", "WAC/BG price in EDI"),
    cancel_column: str | None = "Action",
    hold_column: str | None = "Action",
) -> None:
    """Apply the documented Part E color-coding rules to a written worksheet.

    Formatting is applied strictly after business-rule flags have already
    been computed (Part B); this function never computes new business
    conditions, it only reads existing flag values.

    ``df`` is the internal working dataframe (e.g. ``enriched_df``) that
    still contains the internal flag columns (Controlled_Product,
    Price_Issue, Low_UPS_Inventory), even when those columns have been
    excluded from the written client-facing ``worksheet`` (per the
    authoritative reference schema). Flags are read positionally from
    ``df`` (row order/grain is preserved 1:1 between ``df`` and
    ``worksheet``, since the client-facing Orderbook performs no
    aggregation or row reduction); any business columns still present on
    the worksheet itself (e.g. "Action", price columns) are read directly
    from the worksheet as before.

    Precedence per SOP: a row that is both Controlled Product and Price
    Issue keeps its pink row fill, except the specific price cells are
    overwritten with orange to highlight the pricing problem within an
    otherwise-pink controlled-product row.
    """
    header_to_column_index = {str(cell.value): cell.column for cell in worksheet[1]}

    controlled_series = df[controlled_product_column] if controlled_product_column in df.columns else None
    price_issue_series = df[price_issue_column] if price_issue_column in df.columns else None
    low_inventory_series = df[low_inventory_column] if low_inventory_column in df.columns else None

    price_col_indexes = [header_to_column_index[column] for column in price_columns if column in header_to_column_index]
    cancel_idx = header_to_column_index.get(cancel_column) if cancel_column else None
    hold_idx = header_to_column_index.get(hold_column) if hold_column else None

    df_row_values = df.reset_index(drop=True)

    for row_number in range(2, worksheet.max_row + 1):
        df_index = row_number - 2  # worksheet row 2 == df row 0 (header occupies row 1)
        is_controlled = (
            controlled_series is not None
            and df_index < len(df_row_values)
            and bool(df_row_values[controlled_product_column].iloc[df_index]) is True
        )
        is_price_issue = (
            price_issue_series is not None
            and df_index < len(df_row_values)
            and bool(df_row_values[price_issue_column].iloc[df_index]) is True
        )
        is_low_inventory = (
            low_inventory_series is not None
            and df_index < len(df_row_values)
            and bool(df_row_values[low_inventory_column].iloc[df_index]) is True
        )

        row_fill = None
        if is_controlled:
            row_fill = FILL_CONTROLLED_PRODUCT_PINK
        elif is_low_inventory:
            row_fill = FILL_LOW_INVENTORY_YELLOW

        if row_fill is not None:
            for column_index in range(1, worksheet.max_column + 1):
                worksheet.cell(row=row_number, column=column_index).fill = row_fill

        if is_price_issue:
            for column_index in price_col_indexes:
                worksheet.cell(row=row_number, column=column_index).fill = FILL_PRICE_ISSUE_ORANGE

        # Action-based colors (Cancel = red, Hold = blue). These read an
        # existing "Action" business field if present; no automatic
        # business rule creates or infers this value.
        if cancel_idx is not None:
            action_value = str(worksheet.cell(row=row_number, column=cancel_idx).value or "").strip().lower()
            if action_value == "cancel":
                for column_index in range(1, worksheet.max_column + 1):
                    worksheet.cell(row=row_number, column=column_index).fill = FILL_CANCEL_RED
            elif hold_idx is not None and action_value == "hold":
                for column_index in range(1, worksheet.max_column + 1):
                    worksheet.cell(row=row_number, column=column_index).fill = FILL_HOLD_BLUE


def save_workbook(workbook: Workbook, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if "Sheet" in workbook.sheetnames and len(workbook.sheetnames) > 1:
        default_sheet = workbook["Sheet"]
        if default_sheet.max_row == 1 and default_sheet.max_column == 1 and default_sheet["A1"].value is None:
            workbook.remove(default_sheet)
    workbook.save(output_path)
