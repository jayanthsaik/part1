from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from modules.utils import normalize_identifier_key, normalize_ndc_key, normalize_text_key


@dataclass(frozen=True)
class FinalOrderbookResult:
    """Enriched, row-level dataframe ready for Sales Summary / business rules / Pivot."""

    dataframe: pd.DataFrame
    ups_inventory_matches: int
    moq_matches: int
    sc_comments_matches: int
    sc_comments_missing: int
    buying_group_missing: int
    award_missing: int


def _merge_on_normalized_key(
    left: pd.DataFrame,
    right: pd.DataFrame,
    left_key: str,
    right_key: str,
    value_columns: list[str],
    *,
    mode: str = "identifier",
) -> tuple[pd.DataFrame, int]:
    """Left-join ``right``'s ``value_columns`` onto ``left`` using a normalized key.

    Never drops or duplicates rows from ``left``. Returns the merged
    dataframe and the count of rows that found a match.
    """
    if left_key not in left.columns or right_key not in right.columns:
        result = left.copy()
        for column in value_columns:
            if column not in result.columns:
                result[column] = pd.NA
        return result, 0

    normalizer = normalize_text_key if mode == "text" else (normalize_ndc_key if mode == "ndc" else normalize_identifier_key)

    working_left = left.copy()
    working_right = right[[right_key] + [c for c in value_columns if c in right.columns]].copy()

    working_left["__merge_key__"] = working_left[left_key].apply(normalizer)
    working_right["__merge_key__"] = working_right[right_key].apply(normalizer)
    working_right = working_right.drop(columns=[right_key]).drop_duplicates(subset="__merge_key__", keep="first")

    merged = working_left.merge(working_right, on="__merge_key__", how="left", suffixes=("", "__phase4"))
    match_count = int(merged["__merge_key__"].notna().sum() - merged[value_columns[0]].isna().sum()) if value_columns and value_columns[0] in merged.columns else 0

    merged = merged.drop(columns=["__merge_key__"])
    return merged, match_count


def enrich_master_with_phase2_and_cip(
    master_df: pd.DataFrame,
    ups_inventory_df: Optional[pd.DataFrame],
    moq_validation_df: Optional[pd.DataFrame],
    cip_df: Optional[pd.DataFrame],
    logger,
) -> FinalOrderbookResult:
    """Merge Phase 2 derived results and CIP comments into the Business Master rows.

    Reuses Phase 2's already-computed UPS Inventory and MOQ_Issue values
    (never recalculated). SC Comments are sourced from the CIP workbook by
    NDC, matching the documented business process, since the existing
    Phase 3 master_builder was unable to establish that join (see
    Merge_Audit "No compatible join strategy found").
    """
    working = master_df.copy()

    ups_inventory_matches = 0
    if ups_inventory_df is not None and not ups_inventory_df.empty and "NDC Code" in working.columns and "NDC" in ups_inventory_df.columns:
        working, ups_inventory_matches = _merge_on_normalized_key(
            working,
            ups_inventory_df,
            left_key="NDC Code",
            right_key="NDC",
            value_columns=["UPS Inventory"],
            mode="ndc",
        )
    else:
        working["UPS Inventory"] = pd.NA
        logger.warning("UPS Inventory could not be merged into the final dataset (missing source or key column)")

    moq_matches = 0
    if (
        moq_validation_df is not None
        and not moq_validation_df.empty
        and "Sales Order No." in working.columns
        and "Sales Order" in moq_validation_df.columns
    ):
        working, moq_matches = _merge_on_normalized_key(
            working,
            moq_validation_df,
            left_key="Sales Order No.",
            right_key="Sales Order",
            value_columns=["MOQ_Issue"],
            mode="identifier",
        )
    else:
        working["MOQ_Issue"] = pd.NA
        logger.warning("MOQ_Issue could not be merged into the final dataset (missing source or key column)")

    sc_comments_matches = 0
    if cip_df is not None and not cip_df.empty and "NDC Code" in working.columns and "NDC" in cip_df.columns and "Comments" in cip_df.columns:
        working, sc_comments_matches = _merge_on_normalized_key(
            working,
            cip_df,
            left_key="NDC Code",
            right_key="NDC",
            value_columns=["Comments"],
            mode="ndc",
        )
        working = working.rename(columns={"Comments": "SC Comments"})
    else:
        working["SC Comments"] = pd.NA
        logger.warning("SC Comments could not be merged from CIP (missing source or key column)")

    sc_comments_missing = int(working["SC Comments"].isna().sum())
    buying_group_missing = int(working["Buying Group"].isna().sum()) if "Buying Group" in working.columns else len(working)
    award_missing = int(working["Award Type"].isna().sum()) if "Award Type" in working.columns else len(working)

    logger.info(
        "Phase 4 enrichment stats | ups_inventory_matches=%s | moq_matches=%s | sc_comments_matches=%s | sc_comments_missing=%s | buying_group_missing=%s | award_missing=%s",
        ups_inventory_matches,
        moq_matches,
        sc_comments_matches,
        sc_comments_missing,
        buying_group_missing,
        award_missing,
    )

    return FinalOrderbookResult(
        dataframe=working,
        ups_inventory_matches=ups_inventory_matches,
        moq_matches=moq_matches,
        sc_comments_matches=sc_comments_matches,
        sc_comments_missing=sc_comments_missing,
        buying_group_missing=buying_group_missing,
        award_missing=award_missing,
    )


def merge_historical_sales(
    df: pd.DataFrame,
    historical_df: pd.DataFrame,
    month_labels: tuple[str, ...],
    lookup_column: str,
    logger,
) -> pd.DataFrame:
    """Merge the previous-3-months historical sales + Average onto ``df`` by Lookup."""
    if lookup_column not in df.columns:
        working = df.copy()
        for label in month_labels:
            working[label] = pd.NA
        working["Average"] = pd.NA
        logger.warning("Historical sales could not be merged: '%s' column not found on final dataset", lookup_column)
        return working

    working = df.copy()
    working["__lookup_key__"] = working[lookup_column].apply(normalize_text_key)

    value_columns = list(month_labels) + ["Average"]
    right = historical_df[["__lookup_key__"] + value_columns].copy()

    merged = working.merge(right, on="__lookup_key__", how="left")
    merged = merged.drop(columns=["__lookup_key__"])

    matched = int(merged["Average"].notna().sum())
    missing = int(merged["Average"].isna().sum())
    logger.info("Historical sales merge stats | matched=%s | missing=%s", matched, missing)

    return merged
