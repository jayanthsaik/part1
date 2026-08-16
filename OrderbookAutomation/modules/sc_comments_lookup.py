from __future__ import annotations

"""Dedicated, auditable SC Comments lookup (Critical Inventory Tracker / CIP).

The documented business process populates SC Comments via a VLOOKUP on
NDC against the MOST RECENT Critical Inventory Tracker. This module keeps
NDC as the primary (and only) key, consistent with that documented process,
and adds the auditability the generic merge engine lacked.

Duplicate handling (important):

The documented rule says to use the most recent tracker. The supplied CIP
workbook currently exposes NO date/version/effective-date column, so there
is NO valid deterministic recency rule available inside a single file. This
module therefore does NOT silently keep the first row when one NDC carries
two different comments; it records a DUPLICATE_CONFLICT and leaves the
comment blank. If and when the business supplies a date/version column, it
can be passed via ``source_date_column`` and the most recent record will be
selected deterministically instead.

Guarantees:

- The exact master row count is always preserved.
- Original business columns are never modified; only temporary normalized
  NDC keys are derived.
- Comments are never invented.
- ``SC Comments Lookup Status`` is an internal diagnostic column and is not
  part of the POB output schema.
"""

from dataclasses import dataclass

import pandas as pd

from modules.utils import normalize_ndc_key, normalize_text_key

SC_COMMENTS_STATUS_MATCHED = "MATCHED"
SC_COMMENTS_STATUS_NOT_FOUND = "NOT_FOUND"
SC_COMMENTS_STATUS_DUPLICATE_CONFLICT = "DUPLICATE_CONFLICT"

SC_COMMENTS_STATUS_COLUMN = "SC Comments Lookup Status"
SC_COMMENTS_VALUE_COLUMN = "SC Comments"

SC_COMMENTS_EXCEPTION_COLUMNS = [
    "NDC",
    "Normalized NDC",
    "Customer",
    "Comment(s)",
    "Status",
    "Reason",
]


@dataclass(frozen=True)
class ScCommentsLookupResult:
    dataframe: pd.DataFrame
    exceptions_df: pd.DataFrame
    total_master_rows: int
    master_rows_after_merge: int
    matched_rows: int
    not_found_rows: int
    duplicate_conflict_rows: int
    populated_rows: int
    blank_rows: int
    source_rows: int = 0
    unique_source_ndcs: int = 0
    exact_duplicate_source_rows_removed: int = 0
    conflicting_ndcs: int = 0
    used_date_column: bool = False


def _empty_exceptions_df() -> pd.DataFrame:
    return pd.DataFrame(columns=SC_COMMENTS_EXCEPTION_COLUMNS)


def _blank_result(master_df: pd.DataFrame, reason: str, logger) -> ScCommentsLookupResult:
    logger.warning("SC Comments lookup skipped: %s", reason)
    working = master_df.copy()
    working[SC_COMMENTS_VALUE_COLUMN] = pd.NA
    working[SC_COMMENTS_STATUS_COLUMN] = SC_COMMENTS_STATUS_NOT_FOUND
    total = len(master_df)
    return ScCommentsLookupResult(
        dataframe=working,
        exceptions_df=_empty_exceptions_df(),
        total_master_rows=total,
        master_rows_after_merge=total,
        matched_rows=0,
        not_found_rows=total,
        duplicate_conflict_rows=0,
        populated_rows=0,
        blank_rows=total,
    )


def _build_comment_table(
    cip_df: pd.DataFrame,
    source_ndc_column: str,
    source_comment_column: str,
    source_date_column: str | None,
) -> tuple[pd.DataFrame, int, int, list[dict], bool]:
    """Build a unique normalized-NDC -> Comment table.

    When ``source_date_column`` is present and parseable, the most recent
    record per NDC wins (implementing the documented "most recent tracker"
    rule). Otherwise, conflicting comments for one NDC are flagged as
    DUPLICATE_CONFLICT rather than silently resolved.
    """
    working = cip_df.copy()
    working["__key__"] = working[source_ndc_column].apply(normalize_ndc_key)
    working["__comment_normalized__"] = working[source_comment_column].apply(normalize_text_key)
    working = working[working["__key__"].notna() & working["__comment_normalized__"].notna()]

    used_date_column = False
    if source_date_column and source_date_column in working.columns:
        parsed = pd.to_datetime(working[source_date_column], errors="coerce")
        if parsed.notna().any():
            working["__effective_date__"] = parsed
            used_date_column = True

    before = len(working)
    # Exact duplicates (same NDC AND same comment) are safe to collapse.
    deduped = working.drop_duplicates(subset=["__key__", "__comment_normalized__"], keep="first")
    exact_duplicates_removed = before - len(deduped)

    rows: list[dict] = []
    exceptions: list[dict] = []
    conflicting_ndcs = 0

    for key, group in deduped.groupby("__key__", dropna=True):
        distinct = group["__comment_normalized__"].unique()
        observed = sorted(set(group[source_comment_column].dropna().astype(str)))

        if len(distinct) > 1:
            if used_date_column and group["__effective_date__"].notna().any():
                # Deterministic recency rule available: newest record wins.
                winner = group.sort_values("__effective_date__", ascending=False).iloc[0]
                rows.append(
                    {
                        "__key__": key,
                        "__comment__": winner[source_comment_column],
                        "__status__": SC_COMMENTS_STATUS_MATCHED,
                    }
                )
                exceptions.append(
                    {
                        "NDC": str(group[source_ndc_column].dropna().iloc[0]),
                        "Normalized NDC": key,
                        "Customer": "",
                        "Comment(s)": "; ".join(observed),
                        "Status": SC_COMMENTS_STATUS_MATCHED,
                        "Reason": (
                            "Multiple comments for this NDC; resolved deterministically by most recent "
                            f"'{source_date_column}' value per the documented Critical Inventory Tracker rule"
                        ),
                    }
                )
            else:
                # No valid date/version rule exists -> never silently pick the
                # first row, and never invent a comment.
                conflicting_ndcs += 1
                rows.append({"__key__": key, "__comment__": pd.NA, "__status__": SC_COMMENTS_STATUS_DUPLICATE_CONFLICT})
                exceptions.append(
                    {
                        "NDC": str(group[source_ndc_column].dropna().iloc[0]),
                        "Normalized NDC": key,
                        "Customer": "",
                        "Comment(s)": "; ".join(observed),
                        "Status": SC_COMMENTS_STATUS_DUPLICATE_CONFLICT,
                        "Reason": (
                            "NDC maps to multiple different comments and the Critical Inventory source "
                            "provides no date/version column, so the documented 'most recent tracker' "
                            "rule cannot be applied deterministically"
                        ),
                    }
                )
        else:
            rows.append(
                {
                    "__key__": key,
                    "__comment__": group[source_comment_column].dropna().iloc[0],
                    "__status__": SC_COMMENTS_STATUS_MATCHED,
                }
            )

    table = pd.DataFrame(rows, columns=["__key__", "__comment__", "__status__"])
    return table, exact_duplicates_removed, conflicting_ndcs, exceptions, used_date_column


def build_sc_comments_lookup(
    master_df: pd.DataFrame,
    cip_df: pd.DataFrame | None,
    *,
    master_ndc_column: str,
    master_customer_column: str,
    source_ndc_column: str,
    source_comment_column: str,
    logger,
    source_date_column: str | None = None,
) -> ScCommentsLookupResult:
    """Attach SC Comments to ``master_df`` by NDC, per the documented process."""
    total_master_rows = len(master_df)

    if cip_df is None or cip_df.empty:
        return _blank_result(master_df, "Critical Inventory (CIP) source missing or empty", logger)
    if source_ndc_column not in cip_df.columns or source_comment_column not in cip_df.columns:
        return _blank_result(
            master_df,
            f"CIP source missing required columns ('{source_ndc_column}', '{source_comment_column}')",
            logger,
        )
    if master_ndc_column not in master_df.columns:
        return _blank_result(master_df, f"master column '{master_ndc_column}' not found", logger)

    table, exact_duplicates_removed, conflicting_ndcs, exceptions, used_date_column = _build_comment_table(
        cip_df, source_ndc_column, source_comment_column, source_date_column
    )

    if conflicting_ndcs:
        logger.warning(
            "SC Comments: %s NDC(s) in the Critical Inventory source carry conflicting comments with no "
            "date/version column available; these are flagged DUPLICATE_CONFLICT and left blank rather "
            "than resolved arbitrarily.",
            conflicting_ndcs,
        )

    working = master_df.copy()
    working[SC_COMMENTS_VALUE_COLUMN] = pd.NA
    working[SC_COMMENTS_STATUS_COLUMN] = SC_COMMENTS_STATUS_NOT_FOUND

    if not table.empty:
        assert table["__key__"].is_unique, "SC Comments table must be unique per normalized NDC"
        mapping = table.set_index("__key__")
        keys = working[master_ndc_column].apply(normalize_ndc_key)
        comments = keys.map(mapping["__comment__"])
        statuses = keys.map(mapping["__status__"])

        hit = statuses.notna()
        working.loc[hit, SC_COMMENTS_VALUE_COLUMN] = comments[hit]
        working.loc[hit, SC_COMMENTS_STATUS_COLUMN] = statuses[hit]

    master_rows_after_merge = len(working)
    if master_rows_after_merge != total_master_rows:
        raise ValueError(
            f"SC Comments lookup altered master row count: before={total_master_rows} after={master_rows_after_merge}"
        )

    status_series = working[SC_COMMENTS_STATUS_COLUMN]
    matched_rows = int((status_series == SC_COMMENTS_STATUS_MATCHED).sum())
    not_found_rows = int((status_series == SC_COMMENTS_STATUS_NOT_FOUND).sum())
    duplicate_conflict_rows = int((status_series == SC_COMMENTS_STATUS_DUPLICATE_CONFLICT).sum())
    populated_rows = int(working[SC_COMMENTS_VALUE_COLUMN].notna().sum())
    blank_rows = total_master_rows - populated_rows

    not_found_mask = status_series == SC_COMMENTS_STATUS_NOT_FOUND
    if not_found_mask.any():
        columns = [
            column for column in (master_ndc_column, master_customer_column) if column in working.columns
        ]
        for _, row in working.loc[not_found_mask, columns].drop_duplicates().iterrows():
            ndc_value = row.get(master_ndc_column, "")
            exceptions.append(
                {
                    "NDC": str(ndc_value),
                    "Normalized NDC": normalize_ndc_key(ndc_value),
                    "Customer": row.get(master_customer_column, ""),
                    "Comment(s)": "",
                    "Status": SC_COMMENTS_STATUS_NOT_FOUND,
                    "Reason": "NDC not present in the Critical Inventory (CIP) source",
                }
            )

    exceptions_df = pd.DataFrame(exceptions, columns=SC_COMMENTS_EXCEPTION_COLUMNS)

    logger.info(
        "SC Comments lookup stats | source_rows=%s | unique_source_ndcs=%s | total_master_rows=%s | "
        "rows_after_merge=%s | matched=%s | not_found=%s | duplicate_conflict=%s | populated=%s | "
        "blank=%s | exact_duplicate_source_rows_removed=%s | conflicting_ndcs=%s | used_date_column=%s",
        len(cip_df),
        int(table["__key__"].nunique()) if not table.empty else 0,
        total_master_rows,
        master_rows_after_merge,
        matched_rows,
        not_found_rows,
        duplicate_conflict_rows,
        populated_rows,
        blank_rows,
        exact_duplicates_removed,
        conflicting_ndcs,
        used_date_column,
    )

    return ScCommentsLookupResult(
        dataframe=working,
        exceptions_df=exceptions_df,
        total_master_rows=total_master_rows,
        master_rows_after_merge=master_rows_after_merge,
        matched_rows=matched_rows,
        not_found_rows=not_found_rows,
        duplicate_conflict_rows=duplicate_conflict_rows,
        populated_rows=populated_rows,
        blank_rows=blank_rows,
        source_rows=len(cip_df),
        unique_source_ndcs=int(table["__key__"].nunique()) if not table.empty else 0,
        exact_duplicate_source_rows_removed=exact_duplicates_removed,
        conflicting_ndcs=conflicting_ndcs,
        used_date_column=used_date_column,
    )
