from __future__ import annotations

"""Dedicated, auditable Buying Group lookup.

This module replaces the generic SOURCE_SPECS-driven merge for the Buying
Groups source with a purpose-built, deterministic lookup that:

- normalizes customer names on both sides using the existing centralized
  ``normalize_text_key()`` (never modifying original business columns),
- removes exact-duplicate Customer -> Buying Group source rows before
  joining (never inflating master row count),
- explicitly detects and flags customers whose source rows map to more
  than one DISTINCT Buying Group as "DUPLICATE_CONFLICT" (never guesses),
- always preserves the exact master_df row count (left join on a
  deduplicated, conflict-safe lookup table can never multiply rows),
- exposes a business-facing "Buying Group Lookup Status" column
  (MATCHED / NOT_FOUND / DUPLICATE_CONFLICT),
- produces a diagnostics summary and a "Buying_Group_Exceptions" dataframe
  suitable for its own worksheet.

No other Phase 1-4 business logic (UPS Inventory, MOQ, Sales Summary, POB
layout/formatting, other lookups) is touched by this module.
"""

from dataclasses import dataclass, field

import pandas as pd

from modules.utils import normalize_text_key

BUYING_GROUP_STATUS_MATCHED = "MATCHED"
BUYING_GROUP_STATUS_NOT_FOUND = "NOT_FOUND"
BUYING_GROUP_STATUS_DUPLICATE_CONFLICT = "DUPLICATE_CONFLICT"

BUYING_GROUP_STATUS_COLUMN = "Buying Group Lookup Status"


@dataclass(frozen=True)
class BuyingGroupLookupResult:
    """Result of the dedicated Buying Group lookup."""

    dataframe: pd.DataFrame
    exceptions_df: pd.DataFrame
    total_master_rows: int
    master_rows_after_merge: int
    unique_master_customers: int
    unique_source_customers: int
    exact_duplicate_source_rows_removed: int
    conflicting_customers: int
    matched_customers: int
    not_found_customers: int
    populated_rows: int
    blank_rows: int


def _clean_source_table(
    source_df: pd.DataFrame,
    customer_column: str,
    buying_group_column: str,
) -> tuple[pd.DataFrame, int, list[dict]]:
    """Build a deduplicated, conflict-aware Customer_Normalized -> Buying Group table.

    Returns:
        - a lookup table with columns ["Customer_Normalized", "Customer buying group",
          "__status__"] where "__status__" is MATCHED or DUPLICATE_CONFLICT,
        - the count of exact-duplicate source rows removed,
        - a list of exception dict rows (for conflicting customers), each
          with the original (non-normalized) Customer/Buying Group values
          observed, for the Buying_Group_Exceptions worksheet.
    """
    working = source_df.copy()
    working["Customer_Normalized"] = working[customer_column].apply(normalize_text_key)
    working["Customer_Buying_Group_Normalized"] = working[buying_group_column].apply(normalize_text_key)

    # Keep original (non-normalized) values for exception reporting.
    working = working[[customer_column, buying_group_column, "Customer_Normalized", "Customer_Buying_Group_Normalized"]]

    before_dedup = len(working)
    # Exact duplicates: identical normalized customer AND identical
    # normalized buying group. These are safe to collapse to one row.
    deduped = working.drop_duplicates(subset=["Customer_Normalized", "Customer_Buying_Group_Normalized"], keep="first")
    exact_duplicates_removed = before_dedup - len(deduped)

    exceptions: list[dict] = []
    lookup_rows: list[dict] = []

    for customer_normalized, group in deduped.groupby("Customer_Normalized", dropna=False):
        if pd.isna(customer_normalized):
            continue
        distinct_groups = group["Customer_Buying_Group_Normalized"].dropna().unique()
        if len(distinct_groups) > 1:
            # Conflicting mappings: never guess, never pick first/last.
            observed_customers = sorted(set(group[customer_column].dropna().astype(str)))
            observed_groups = sorted(set(group[buying_group_column].dropna().astype(str)))
            exceptions.append(
                {
                    "Customer": "; ".join(observed_customers),
                    "Normalized Customer": customer_normalized,
                    "Buying Group(s)": "; ".join(observed_groups),
                    "Status": BUYING_GROUP_STATUS_DUPLICATE_CONFLICT,
                    "Reason": "Customer maps to multiple different Buying Group values in the source workbook",
                }
            )
            lookup_rows.append(
                {
                    "Customer_Normalized": customer_normalized,
                    "Customer buying group": pd.NA,
                    "__status__": BUYING_GROUP_STATUS_DUPLICATE_CONFLICT,
                }
            )
        else:
            buying_group_value = group[buying_group_column].dropna().iloc[0] if not group[buying_group_column].dropna().empty else pd.NA
            lookup_rows.append(
                {
                    "Customer_Normalized": customer_normalized,
                    "Customer buying group": buying_group_value,
                    "__status__": BUYING_GROUP_STATUS_MATCHED,
                }
            )

    lookup_table = pd.DataFrame(lookup_rows, columns=["Customer_Normalized", "Customer buying group", "__status__"])
    return lookup_table, exact_duplicates_removed, exceptions


def build_buying_group_lookup(
    master_df: pd.DataFrame,
    buying_groups_df: pd.DataFrame | None,
    *,
    master_customer_column: str,
    source_customer_column: str,
    source_buying_group_column: str,
    logger,
) -> BuyingGroupLookupResult:
    """Deterministically join Buying Group onto ``master_df`` without altering row count.

    ``master_df``'s ``master_customer_column`` (e.g. "Sold-to party Name")
    and the source's ``source_customer_column`` (e.g. "Customer") are never
    modified; only temporary normalized keys are used for matching.
    """
    total_master_rows = len(master_df)
    working = master_df.copy()

    if master_customer_column not in working.columns:
        logger.warning(
            "Buying Group lookup skipped: master column '%s' not found on master dataframe",
            master_customer_column,
        )
        working["Customer buying group"] = pd.NA
        working[BUYING_GROUP_STATUS_COLUMN] = BUYING_GROUP_STATUS_NOT_FOUND
        exceptions_df = pd.DataFrame(columns=["Customer", "Normalized Customer", "Buying Group(s)", "Status", "Reason"])
        return BuyingGroupLookupResult(
            dataframe=working,
            exceptions_df=exceptions_df,
            total_master_rows=total_master_rows,
            master_rows_after_merge=len(working),
            unique_master_customers=0,
            unique_source_customers=0,
            exact_duplicate_source_rows_removed=0,
            conflicting_customers=0,
            matched_customers=0,
            not_found_customers=total_master_rows,
            populated_rows=0,
            blank_rows=total_master_rows,
        )

    if (
        buying_groups_df is None
        or buying_groups_df.empty
        or source_customer_column not in buying_groups_df.columns
        or source_buying_group_column not in buying_groups_df.columns
    ):
        logger.warning("Buying Group lookup skipped: source dataframe missing, empty, or missing required columns")
        working["Customer buying group"] = pd.NA
        working[BUYING_GROUP_STATUS_COLUMN] = BUYING_GROUP_STATUS_NOT_FOUND
        exceptions_df = pd.DataFrame(columns=["Customer", "Normalized Customer", "Buying Group(s)", "Status", "Reason"])
        unique_master_customers = int(working[master_customer_column].apply(normalize_text_key).dropna().nunique())
        return BuyingGroupLookupResult(
            dataframe=working,
            exceptions_df=exceptions_df,
            total_master_rows=total_master_rows,
            master_rows_after_merge=len(working),
            unique_master_customers=unique_master_customers,
            unique_source_customers=0,
            exact_duplicate_source_rows_removed=0,
            conflicting_customers=0,
            matched_customers=0,
            not_found_customers=total_master_rows,
            populated_rows=0,
            blank_rows=total_master_rows,
        )

    lookup_table, exact_duplicates_removed, conflict_exceptions = _clean_source_table(
        buying_groups_df, source_customer_column, source_buying_group_column
    )

    # STEP 6 validation: for all non-conflicting records, Customer_Normalized
    # must map to a UNIQUE Buying Group. By construction of _clean_source_table
    # (one row per Customer_Normalized after groupby), this is guaranteed;
    # assert defensively for auditability.
    non_conflict_rows = lookup_table[lookup_table["__status__"] == BUYING_GROUP_STATUS_MATCHED]
    assert non_conflict_rows["Customer_Normalized"].is_unique, (
        "Internal invariant violated: non-conflicting Buying Group lookup table must have a unique "
        "Customer_Normalized -> Buying Group mapping"
    )

    working["Sold_To_Party_Name_Normalized"] = working[master_customer_column].apply(normalize_text_key)

    merged = working.merge(
        lookup_table,
        left_on="Sold_To_Party_Name_Normalized",
        right_on="Customer_Normalized",
        how="left",
        suffixes=("", "__buying_group_source"),
    )

    # STEP 5: row count MUST be preserved exactly.
    master_rows_after_merge = len(merged)
    if master_rows_after_merge != total_master_rows:
        raise ValueError(
            f"Buying Group merge altered master row count: before={total_master_rows} after={master_rows_after_merge}. "
            "This indicates a non-unique lookup key slipped through deduplication."
        )

    status = merged["__status__"]
    lookup_status = status.where(status.notna(), BUYING_GROUP_STATUS_NOT_FOUND)
    merged[BUYING_GROUP_STATUS_COLUMN] = lookup_status

    merged = merged.drop(columns=["Sold_To_Party_Name_Normalized", "Customer_Normalized", "__status__"], errors="ignore")

    populated_rows = int(merged["Customer buying group"].notna().sum())
    blank_rows = total_master_rows - populated_rows

    matched_customers = int((lookup_status == BUYING_GROUP_STATUS_MATCHED).sum())
    not_found_customers = int((lookup_status == BUYING_GROUP_STATUS_NOT_FOUND).sum())
    conflicting_rows_in_master = int((lookup_status == BUYING_GROUP_STATUS_DUPLICATE_CONFLICT).sum())

    unique_master_customers = int(working[master_customer_column].apply(normalize_text_key).dropna().nunique())
    unique_source_customers = int(lookup_table["Customer_Normalized"].dropna().nunique())
    conflicting_customers = int((lookup_table["__status__"] == BUYING_GROUP_STATUS_DUPLICATE_CONFLICT).sum())

    # STEP 10 / STEP 14: build the NOT_FOUND exceptions too (customers on
    # the master side that never matched any source row), in addition to
    # the DUPLICATE_CONFLICT exceptions already collected.
    not_found_customers_normalized = sorted(
        set(
            merged.loc[lookup_status == BUYING_GROUP_STATUS_NOT_FOUND, master_customer_column]
            .dropna()
            .astype(str)
        )
    )
    not_found_exceptions = [
        {
            "Customer": customer,
            "Normalized Customer": normalize_text_key(customer),
            "Buying Group(s)": "",
            "Status": BUYING_GROUP_STATUS_NOT_FOUND,
            "Reason": "Customer not present in Buying Groups source workbook",
        }
        for customer in not_found_customers_normalized
    ]

    exceptions_df = pd.DataFrame(
        conflict_exceptions + not_found_exceptions,
        columns=["Customer", "Normalized Customer", "Buying Group(s)", "Status", "Reason"],
    )

    logger.info(
        "Buying Group lookup stats | total_master_rows=%s | master_rows_after_merge=%s | "
        "unique_master_customers=%s | unique_source_customers=%s | exact_duplicate_source_rows_removed=%s | "
        "conflicting_customers=%s | matched_rows=%s | not_found_rows=%s | duplicate_conflict_rows=%s | "
        "populated_rows=%s | blank_rows=%s",
        total_master_rows,
        master_rows_after_merge,
        unique_master_customers,
        unique_source_customers,
        exact_duplicates_removed,
        conflicting_customers,
        matched_customers,
        not_found_customers,
        conflicting_rows_in_master,
        populated_rows,
        blank_rows,
    )

    return BuyingGroupLookupResult(
        dataframe=merged,
        exceptions_df=exceptions_df,
        total_master_rows=total_master_rows,
        master_rows_after_merge=master_rows_after_merge,
        unique_master_customers=unique_master_customers,
        unique_source_customers=unique_source_customers,
        exact_duplicate_source_rows_removed=exact_duplicates_removed,
        conflicting_customers=conflicting_customers,
        matched_customers=matched_customers,
        not_found_customers=not_found_customers,
        populated_rows=populated_rows,
        blank_rows=blank_rows,
    )
