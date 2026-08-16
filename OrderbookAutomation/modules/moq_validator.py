from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from config import SALES_SUMMARY_COLUMNS
from modules.utils import coerce_numeric_column


@dataclass(frozen=True)
class MoqValidationResult:
    """MOQ validation output and summary metrics."""

    dataframe: pd.DataFrame
    failure_count: int


def build_moq_validation(source_df: pd.DataFrame, logger) -> MoqValidationResult:
    """Flag MOQ issues where sales order quantity is not an integer multiple of pack size."""
    sales_order_col = SALES_SUMMARY_COLUMNS["sales_order_number"]
    material_col = SALES_SUMMARY_COLUMNS["material_code"]
    pack_size_col = SALES_SUMMARY_COLUMNS["pack_size"]
    sales_order_qty_col = SALES_SUMMARY_COLUMNS["sales_order_qty"]

    required = [sales_order_col, material_col, pack_size_col, sales_order_qty_col]
    missing = [column for column in required if column not in source_df.columns]
    if missing:
        raise ValueError(f"MOQ validation source dataframe is missing required columns: {', '.join(missing)}")

    working = source_df.copy()
    working[pack_size_col] = coerce_numeric_column(working[pack_size_col])
    working[sales_order_qty_col] = coerce_numeric_column(working[sales_order_qty_col])

    missing_pack_size = int(working[pack_size_col].isna().sum())
    if missing_pack_size > 0:
        logger.warning("Missing Pack Size values for MOQ validation: %s", missing_pack_size)

    missing_sales_qty = int(working[sales_order_qty_col].isna().sum())
    if missing_sales_qty > 0:
        logger.warning("Missing Sales Qty values for MOQ validation: %s", missing_sales_qty)

    zero_pack_size = int((working[pack_size_col] == 0).fillna(False).sum())
    if zero_pack_size > 0:
        logger.warning("Division by zero risk from Pack Size values equal to zero: %s", zero_pack_size)

    valid_mask = (
        working[pack_size_col].notna()
        & working[sales_order_qty_col].notna()
        & (working[pack_size_col] != 0)
    )
    quotient = pd.Series(pd.NA, index=working.index, dtype="Float64")
    quotient.loc[valid_mask] = working.loc[valid_mask, sales_order_qty_col] / working.loc[valid_mask, pack_size_col]

    working["MOQ_Issue"] = True
    working.loc[valid_mask, "MOQ_Issue"] = (quotient.loc[valid_mask] % 1 != 0).fillna(True)

    failure_count = int(working["MOQ_Issue"].fillna(True).sum())
    logger.info(
        "MOQ validation stats | total_rows=%s | values_normalized=%s | successful_matches=%s | unmatched_records=%s | duplicate_lookup_keys=%s",
        len(working),
        0,
        int(valid_mask.sum()),
        int((~valid_mask).sum()),
        0,
    )

    result_df = working[[sales_order_col, material_col, pack_size_col, sales_order_qty_col, "MOQ_Issue"]].copy()
    result_df = result_df.rename(
        columns={
            sales_order_col: "Sales Order",
            material_col: "Material",
            pack_size_col: "Pack Size",
            sales_order_qty_col: "Sales Order Qty",
        }
    )
    return MoqValidationResult(dataframe=result_df, failure_count=failure_count)