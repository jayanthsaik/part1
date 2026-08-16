from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from config import ORDERBOOK_COLUMNS, SALES_SUMMARY_COLUMNS
from modules.utils import normalize_ndc_key, normalize_text_key


@dataclass(frozen=True)
class LookupKeyResult:
    """Lookup key dataset and supporting metrics."""

    dataframe: pd.DataFrame
    total_rows: int
    values_normalized: int
    duplicate_lookup_keys: int


def build_lookup_keys(source_df: pd.DataFrame, logger) -> LookupKeyResult:
    """Build normalized internal lookup keys without altering original business columns."""
    ndc_column = _resolve_column(source_df, SALES_SUMMARY_COLUMNS["ndc_code"], ORDERBOOK_COLUMNS["ndc_code"])
    sold_to_party_column = _resolve_column(source_df, SALES_SUMMARY_COLUMNS["sold_to_party"], ORDERBOOK_COLUMNS["sold_to_party"])
    sold_to_party_name_column = _resolve_column(
        source_df,
        SALES_SUMMARY_COLUMNS["sold_to_party_name"],
        ORDERBOOK_COLUMNS["sold_to_party_name"],
    )

    working = source_df.copy()
    working["__ndc_key__"] = working[ndc_column].apply(normalize_ndc_key).astype("string")
    working["__sold_to_name_key__"] = working[sold_to_party_name_column].apply(normalize_text_key).astype("string")
    working["Lookup"] = working["__ndc_key__"].fillna("") + working["__sold_to_name_key__"].fillna("")
    working["Lookup"] = working["Lookup"].replace("", pd.NA)

    values_normalized = _count_changes(working[ndc_column], working["__ndc_key__"]) + _count_changes(
        working[sold_to_party_name_column],
        working["__sold_to_name_key__"],
    )
    duplicate_lookup_keys = int(working["Lookup"].dropna().duplicated().sum())

    logger.info(
        "Lookup key stats | total_rows=%s | values_normalized=%s | successful_matches=%s | unmatched_records=%s | duplicate_lookup_keys=%s",
        len(working),
        values_normalized,
        len(working),
        0,
        duplicate_lookup_keys,
    )

    result_df = working[["Lookup", ndc_column, sold_to_party_column, sold_to_party_name_column]].copy()
    result_df = result_df.rename(
        columns={
            ndc_column: "NDC",
            sold_to_party_column: "Sold-to Party",
            sold_to_party_name_column: "Sold-to Party Name",
        }
    )
    return LookupKeyResult(
        dataframe=result_df,
        total_rows=len(result_df),
        values_normalized=values_normalized,
        duplicate_lookup_keys=duplicate_lookup_keys,
    )


def _resolve_column(df: pd.DataFrame, primary: str, fallback: str) -> str:
    """Resolve the preferred business column name with a backward-compatible fallback."""
    if primary in df.columns:
        return primary
    if fallback in df.columns:
        return fallback
    raise ValueError(f"Required column not found. Expected one of: {primary}, {fallback}")


def _count_changes(original: pd.Series, normalized: pd.Series) -> int:
    """Count values whose normalized form differs from the original business value."""
    original_text = original.astype("string").str.strip()
    normalized_text = normalized.astype("string")
    return int((original_text.notna() & normalized_text.notna() & (original_text != normalized_text)).sum())