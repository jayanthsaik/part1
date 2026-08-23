from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pandas as pd


@dataclass(frozen=True)
class AggregationResult:
    """Result of the documented Sales Summary / Pivot aggregation."""

    dataframe: pd.DataFrame
    row_count: int
    unique_lookup_count: int
    duplicate_lookup_count: int


# Documented Pivot/Sales Summary structure (Steps 4 and Part C).
ROW_COLUMNS: tuple[str, ...] = (
    "Material Description",
    "Sold-to party Name",
    "Lookup",
    "NDC Code",
)

# (source_column, aggregation_function, output_column_name)
VALUE_AGGREGATIONS: tuple[tuple[str, str, str], ...] = (
    ("UPS Inventory", "max", "Max of UPS Inventory"),
    ("Sales Order Qty", "sum", "Sum of Sales Order Qty"),
    ("Sales Qty MTD", "max", "Max of Sales Qty MTD"),
    ("Forecast Qty", "max", "Max of Forecast Qty"),
)

# INTERNAL diagnostic column (never part of the client-facing reference
# Summary schema). Carries the aggregated Action state for one summary row
# so the Summary sheet can reproduce the Orderbook sheet's red/blue row
# colouring at the aggregated grain.
SUMMARY_ACTION_FLAG_COLUMN = "Summary_Action_Flag"

SUMMARY_ACTION_CANCEL = "Cancel"
SUMMARY_ACTION_HOLD = "Hold"

# Source column on the detail (order/item grain) dataframe.
ACTION_SOURCE_COLUMN = "Action"

_CANCEL_TEMP_COLUMN = "__any_cancel__"
_HOLD_TEMP_COLUMN = "__any_hold__"


def build_sales_summary_aggregation(df: pd.DataFrame, logger) -> AggregationResult:
    """Aggregate ``df`` using the documented Sales Summary / Pivot structure.

    ROWS: Material Description, Sold-to party Name, Lookup, NDC Code
    VALUES: UPS Inventory -> MAX, Sales Order Qty -> SUM,
            Sales Qty MTD -> MAX, Forecast Qty -> MAX

    Additionally rolls the detail-grain "Action" field up into the internal
    ``Summary_Action_Flag`` column so the Summary sheet can reproduce the
    Orderbook sheet's Cancel/Hold row colouring at the aggregated grain.

    ROLLUP RULE (mirrors the Orderbook sheet's own precedence, where the
    Cancel branch is evaluated before the Hold branch): if ANY detail row in
    the group is "Cancel" the group is Cancel; otherwise if ANY detail row
    is "Hold" the group is Hold; otherwise the flag is null. Cancel wins
    because it is the more severe/irreversible state -- a summary row that
    contains even one cancelled line must never be shown as merely on hold.

    Implemented entirely with pandas groupby/agg (no Excel Pivot Table).
    """
    missing_row_columns = [column for column in ROW_COLUMNS if column not in df.columns]
    if missing_row_columns:
        raise ValueError(f"Cannot build Sales Summary aggregation; missing required column(s): {missing_row_columns}")

    working = df.copy()

    agg_spec: dict[str, str] = {}
    rename_spec: dict[str, str] = {}
    for source_column, agg_function, output_name in VALUE_AGGREGATIONS:
        if source_column in working.columns:
            agg_spec[source_column] = agg_function
            rename_spec[source_column] = output_name
        else:
            logger.warning("Sales Summary aggregation: value column '%s' not found; output column '%s' will be blank", source_column, output_name)

    # Derive per-detail-row boolean Cancel/Hold indicators BEFORE grouping so
    # they can be aggregated inside the SAME groupby call. This guarantees
    # the flag stays perfectly row-aligned with the aggregated output (a
    # separate groupby could reorder rows).
    has_action_column = ACTION_SOURCE_COLUMN in working.columns
    if has_action_column:
        normalized_action = working[ACTION_SOURCE_COLUMN].astype("string").str.strip().str.casefold()
        working[_CANCEL_TEMP_COLUMN] = normalized_action.eq("cancel").fillna(False)
        working[_HOLD_TEMP_COLUMN] = normalized_action.eq("hold").fillna(False)
        agg_spec[_CANCEL_TEMP_COLUMN] = "any"
        agg_spec[_HOLD_TEMP_COLUMN] = "any"
    else:
        logger.warning(
            "Sales Summary aggregation: '%s' column not found; Summary Cancel/Hold row colouring will be skipped",
            ACTION_SOURCE_COLUMN,
        )

    grouped = working.groupby(list(ROW_COLUMNS), dropna=False, as_index=False).agg(agg_spec)
    grouped = grouped.rename(columns=rename_spec)

    # Collapse the two booleans into a single flag, Cancel taking precedence.
    if has_action_column:
        grouped[SUMMARY_ACTION_FLAG_COLUMN] = pd.NA
        grouped.loc[grouped[_HOLD_TEMP_COLUMN], SUMMARY_ACTION_FLAG_COLUMN] = SUMMARY_ACTION_HOLD
        grouped.loc[grouped[_CANCEL_TEMP_COLUMN], SUMMARY_ACTION_FLAG_COLUMN] = SUMMARY_ACTION_CANCEL
        cancel_rows = int(grouped[_CANCEL_TEMP_COLUMN].sum())
        hold_rows = int((grouped[_HOLD_TEMP_COLUMN] & ~grouped[_CANCEL_TEMP_COLUMN]).sum())
        grouped = grouped.drop(columns=[_CANCEL_TEMP_COLUMN, _HOLD_TEMP_COLUMN])
    else:
        grouped[SUMMARY_ACTION_FLAG_COLUMN] = pd.NA
        cancel_rows = 0
        hold_rows = 0

    for _, _, output_name in VALUE_AGGREGATIONS:
        if output_name not in grouped.columns:
            grouped[output_name] = pd.NA

    ordered_columns = (
        list(ROW_COLUMNS)
        + [output_name for _, _, output_name in VALUE_AGGREGATIONS]
        + [SUMMARY_ACTION_FLAG_COLUMN]
    )
    grouped = grouped[ordered_columns]

    duplicate_lookup_count = int(grouped["Lookup"].dropna().duplicated().sum())
    unique_lookup_count = int(grouped["Lookup"].nunique(dropna=True))

    logger.info(
        "Sales Summary aggregation stats | rows=%s | unique_lookups=%s | duplicate_lookups=%s | "
        "action_cancel_rows=%s | action_hold_rows=%s",
        len(grouped),
        unique_lookup_count,
        duplicate_lookup_count,
        cancel_rows,
        hold_rows,
    )

    return AggregationResult(
        dataframe=grouped,
        row_count=len(grouped),
        unique_lookup_count=unique_lookup_count,
        duplicate_lookup_count=duplicate_lookup_count,
    )
