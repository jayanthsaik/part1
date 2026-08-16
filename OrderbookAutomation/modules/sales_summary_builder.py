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


def build_sales_summary_aggregation(df: pd.DataFrame, logger) -> AggregationResult:
    """Aggregate ``df`` using the documented Sales Summary / Pivot structure.

    ROWS: Material Description, Sold-to party Name, Lookup, NDC Code
    VALUES: UPS Inventory -> MAX, Sales Order Qty -> SUM,
            Sales Qty MTD -> MAX, Forecast Qty -> MAX

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

    grouped = working.groupby(list(ROW_COLUMNS), dropna=False, as_index=False).agg(agg_spec)
    grouped = grouped.rename(columns=rename_spec)

    for _, _, output_name in VALUE_AGGREGATIONS:
        if output_name not in grouped.columns:
            grouped[output_name] = pd.NA

    ordered_columns = list(ROW_COLUMNS) + [output_name for _, _, output_name in VALUE_AGGREGATIONS]
    grouped = grouped[ordered_columns]

    duplicate_lookup_count = int(grouped["Lookup"].dropna().duplicated().sum())
    unique_lookup_count = int(grouped["Lookup"].nunique(dropna=True))

    logger.info(
        "Sales Summary aggregation stats | rows=%s | unique_lookups=%s | duplicate_lookups=%s",
        len(grouped),
        unique_lookup_count,
        duplicate_lookup_count,
    )

    return AggregationResult(
        dataframe=grouped,
        row_count=len(grouped),
        unique_lookup_count=unique_lookup_count,
        duplicate_lookup_count=duplicate_lookup_count,
    )
