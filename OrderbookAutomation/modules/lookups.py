from __future__ import annotations

import pandas as pd

from config import LOOKUP_COLUMNS
from modules.utils import normalize_identifier_key


def enrich_orderbook_with_lookup(
    orderbook_df: pd.DataFrame,
    lookup_df: pd.DataFrame,
    *,
    logger=None,
    debug_keep_temp_keys: bool = False,
) -> pd.DataFrame:
    lookup_material = LOOKUP_COLUMNS["material_code"]
    lookup_description = LOOKUP_COLUMNS["material_description"]
    lookup_pack_size = LOOKUP_COLUMNS["pack_size_moq"]

    if lookup_material not in orderbook_df.columns or lookup_material not in lookup_df.columns:
        enriched = orderbook_df.copy()
        if lookup_description not in enriched.columns:
            enriched[lookup_description] = pd.NA
        if lookup_pack_size not in enriched.columns:
            enriched[lookup_pack_size] = pd.NA
        return enriched

    left = orderbook_df.copy()
    right = lookup_df.copy()

    left_key_col = "__lookup_material_key_left__"
    right_key_col = "__lookup_material_key_right__"
    left[left_key_col] = left[lookup_material].apply(normalize_identifier_key).astype("string")
    right[right_key_col] = right[lookup_material].apply(normalize_identifier_key).astype("string")

    left_changes = _count_normalized_values(left[lookup_material], left[left_key_col])
    right_changes = _count_normalized_values(right[lookup_material], right[right_key_col])

    lookup_columns = [
        column
        for column in [
            right_key_col,
            LOOKUP_COLUMNS["ndc_code"],
            lookup_description,
            lookup_pack_size,
        ]
        if column in right.columns
    ]
    duplicate_lookup_keys = int(right[right_key_col].dropna().duplicated().sum())
    lookup_subset = right[lookup_columns].copy().drop_duplicates(subset=[right_key_col], keep="first")

    merged = left.merge(lookup_subset, left_on=left_key_col, right_on=right_key_col, how="left", indicator=True)

    successful_matches = int((merged[left_key_col].notna() & (merged["_merge"] == "both")).sum())
    unmatched_records = int((merged[left_key_col].notna() & (merged["_merge"] != "both")).sum())

    if logger is not None:
        logger.info(
            "Material lookup stats | total_rows=%s | values_normalized=%s | successful_matches=%s | unmatched_records=%s | duplicate_lookup_keys=%s",
            len(left),
            left_changes + right_changes,
            successful_matches,
            unmatched_records,
            duplicate_lookup_keys,
        )

    drop_columns = ["_merge", right_key_col]
    if not debug_keep_temp_keys:
        drop_columns.append(left_key_col)
    merged = merged.drop(columns=[column for column in drop_columns if column in merged.columns], errors="ignore")
    return merged


def _count_normalized_values(original: pd.Series, normalized: pd.Series) -> int:
    original_as_text = original.astype("string").str.strip()
    normalized_as_text = normalized.astype("string")
    changed = original_as_text.notna() & normalized_as_text.notna() & (original_as_text != normalized_as_text)
    return int(changed.sum())
