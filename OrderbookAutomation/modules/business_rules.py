from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pandas as pd

from modules.utils import coerce_numeric_column

# Controlled product keyword list, per the documented SOP. Matching is
# case-insensitive substring matching against "Material Description".
CONTROLLED_PRODUCT_KEYWORDS: tuple[str, ...] = (
    "APAP/Codeine",
    "APAP",
    "Hydro",
    "Codeine",
    "BAC",
    "Gabapentin",
    "Hydro/Apap",
    "Oxycodone",
    "sevel",
    "Phenobarbital",
    "Testosterone",
    "Tramadol",
    "Hydro bit ",
    "hydro bitrate",
    "Zolpidem",
)

LOW_UPS_INVENTORY_THRESHOLD = 10_000


@dataclass(frozen=True)
class BusinessRuleStats:
    """Summary counters for the business rule engine run."""

    controlled_product_count: int
    price_issue_count: int
    moq_issue_count: int
    low_ups_inventory_count: int


def flag_controlled_products(df: pd.DataFrame, material_description_column: str) -> pd.Series:
    """Return a boolean Series flagging rows whose material description matches a controlled product keyword."""
    if material_description_column not in df.columns:
        return pd.Series(False, index=df.index)

    descriptions = df[material_description_column].astype("string").fillna("")
    pattern = "|".join(_escape_keyword(keyword) for keyword in CONTROLLED_PRODUCT_KEYWORDS)
    return descriptions.str.contains(pattern, case=False, regex=True, na=False)


def _escape_keyword(keyword: str) -> str:
    import re

    return re.escape(keyword)


def flag_price_issues(
    df: pd.DataFrame,
    unit_price_column: str,
    wac_bg_price_column: str,
) -> tuple[pd.Series, pd.Series]:
    """Return (Price_Issue, Price_Difference) Series per documented Rule 2.

    Price_Issue is True when Unit Price is exactly 0.00, OR when Unit Price
    differs from WAC/BG price in EDI (a pricing discrepancy).
    """
    if unit_price_column not in df.columns or wac_bg_price_column not in df.columns:
        price_issue = pd.Series(False, index=df.index)
        price_difference = pd.Series(pd.NA, index=df.index, dtype="Float64")
        return price_issue, price_difference

    unit_price = coerce_numeric_column(df[unit_price_column])
    wac_bg_price = coerce_numeric_column(df[wac_bg_price_column])

    price_difference = unit_price - wac_bg_price

    zero_price = unit_price.fillna(0) == 0
    discrepancy = (price_difference.fillna(0) != 0) & unit_price.notna() & wac_bg_price.notna()

    price_issue = (zero_price | discrepancy).fillna(True)
    return price_issue, price_difference


def flag_low_ups_inventory(df: pd.DataFrame, ups_inventory_column: str) -> pd.Series:
    """Return a boolean Series flagging rows where UPS Inventory < 10,000 (Rule 4)."""
    if ups_inventory_column not in df.columns:
        return pd.Series(False, index=df.index)
    ups_inventory = coerce_numeric_column(df[ups_inventory_column])
    return (ups_inventory < LOW_UPS_INVENTORY_THRESHOLD).fillna(False)


_MOQ_TOLERANCE = 1e-6


def _compute_moq_issue_series(df: pd.DataFrame, qty_col: str = "Sales Order Qty", moq_col: str = "Pack Size (MOQ)") -> pd.Series:
    """Return boolean Series marking rows where qty / moq is not an integer.
    Missing/zero MOQ or non-numeric values are treated as NOT an issue.
    """
    qty = coerce_numeric_column(df.get(qty_col, pd.Series(dtype="float"))).fillna(0)
    moq = coerce_numeric_column(df.get(moq_col, pd.Series(dtype="float")))
    result = pd.Series(False, index=qty.index)

    valid = moq.notna() & (moq != 0) & qty.notna()
    if not valid.any():
        return result

    q = qty.loc[valid] / moq.loc[valid]
    frac = (q % 1).abs()
    issue_mask = (frac > _MOQ_TOLERANCE) & ((1 - frac) > _MOQ_TOLERANCE)
    result.loc[valid] = issue_mask
    return result


def apply_business_rules(
    df: pd.DataFrame,
    *,
    material_description_column: str,
    unit_price_column: str,
    wac_bg_price_column: str,
    ups_inventory_column: str,
    moq_issue_column: str,
    logger,
) -> tuple[pd.DataFrame, BusinessRuleStats]:
    """Apply all Phase 4 Part B business rules to ``df`` and return flag columns.

    Reuses MOQ_Issue values already computed in Phase 2 (Rule 3) rather than
    recalculating them. SC Comments, Buying Group, and Award are reused
    as-is from Phase 3 enrichment (Rules 5-7) and are not modified here.
    Avinash/Krishna Comments (Rule 8) is created blank only, never populated
    automatically and never used to drive any rule or formatting decision.
    """
    working = df.copy()

    working["Controlled_Product"] = flag_controlled_products(working, material_description_column)

    price_issue, price_difference = flag_price_issues(working, unit_price_column, wac_bg_price_column)
    working["Price_Issue"] = price_issue
    working["Price_Difference"] = price_difference

    # Always compute MOQ issue from the raw Orderbook columns (Sales Order Qty ÷ Pack Size (MOQ)).
    # Do NOT reuse the Phase‑2 / sales_summary MOQ_Issue column — compute from the actual Orderbook values.
    if moq_issue_column in working.columns:
        logger.info(
            "Phase 2 MOQ_Issue column '%s' present but ignored; computing MOQ issues from Orderbook columns",
            moq_issue_column,
        )
    working["MOQ_Issue"] = _compute_moq_issue_series(working)

    working["Low_UPS_Inventory"] = flag_low_ups_inventory(working, ups_inventory_column)

    # Manual-only field: created blank, never auto-populated, never used to
    # drive business logic or Excel formatting.
    if "Avinash/Krishna Comments" not in working.columns:
        working["Avinash/Krishna Comments"] = pd.NA

    stats = BusinessRuleStats(
        controlled_product_count=int(working["Controlled_Product"].sum()),
        price_issue_count=int(working["Price_Issue"].sum()),
        moq_issue_count=int(working["MOQ_Issue"].astype(bool).sum()),
        low_ups_inventory_count=int(working["Low_UPS_Inventory"].sum()),
    )

    logger.info(
        "Business rules applied | controlled_products=%s | price_issues=%s | moq_issues=%s | low_ups_inventory=%s",
        stats.controlled_product_count,
        stats.price_issue_count,
        stats.moq_issue_count,
        stats.low_ups_inventory_count,
    )

    return working, stats
