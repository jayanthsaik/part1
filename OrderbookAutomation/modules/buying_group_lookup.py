from __future__ import annotations

"""Dedicated, auditable, multi-source Buying Group enrichment.

``Buying_groups.xlsx`` is only ONE of several workbooks supplied to the
application that carry a Customer -> Buying Group mapping, and it is known
to be incomplete (e.g. "KROGER" is absent from it but present in
``Strend.xlsx``). This module therefore consolidates EVERY authoritative
mapping source declared in ``config.BUYING_GROUP_SOURCES`` into a single
internal Buying Group master, then resolves each customer deterministically
by source priority.

Guarantees:

- Customer names are matched via the existing centralized
  ``normalize_text_key()`` (handles case, leading/trailing whitespace,
  repeated spaces, tabs, line breaks and hidden characters). Original
  business columns are NEVER modified -- only temporary normalized keys.
- Exact duplicates (same normalized customer AND same normalized Buying
  Group) are collapsed, within and across sources, so master rows can never
  be multiplied.
- Cross-source disagreements are resolved by source priority (priority 1
  wins). This is a deterministic resolution, NOT a conflict; the losing
  value is recorded as a "lower-priority disagreement" in the audit trail.
- DUPLICATE_CONFLICT is raised ONLY when a single priority tier maps one
  normalized customer to two or more distinct Buying Group values, because
  only then is there no deterministic rule available to choose between them.
  In that case the Buying Group is left blank -- values are never invented.
- A fallback match from a lower-priority source is still MATCHED. Absence
  from the primary Buying Groups file alone never yields NOT_FOUND.
- NOT_FOUND is only assigned after ALL configured sources have been checked.
- The exact master row count is always preserved.
- ``Buying Group Lookup Status`` and ``Buying Group Source`` are internal
  lineage/diagnostic columns; they are not part of the POB output schema.

No other Phase 1-4 business logic (canonical Lookup construction, UPS
Inventory, MOQ, Sales Summary, Awards, POB layout/formatting) is touched.
"""

from dataclasses import dataclass, field
from typing import Sequence

import pandas as pd

from modules.utils import normalize_text_key

BUYING_GROUP_STATUS_MATCHED = "MATCHED"
BUYING_GROUP_STATUS_NOT_FOUND = "NOT_FOUND"
BUYING_GROUP_STATUS_DUPLICATE_CONFLICT = "DUPLICATE_CONFLICT"
BUYING_GROUP_STATUS_LOWER_PRIORITY_DISAGREEMENT = "LOWER_PRIORITY_DISAGREEMENT"

BUYING_GROUP_STATUS_COLUMN = "Buying Group Lookup Status"
BUYING_GROUP_SOURCE_COLUMN = "Buying Group Source"
BUYING_GROUP_VALUE_COLUMN = "Customer buying group"
# Downstream Phase 4 (Summary layout / POB) consumes the business-facing
# column name "Buying Group", while the master/source schema uses
# "Customer buying group". The enrichment layer publishes BOTH names with
# the identical resolved value so the value actually reaches the POB
# Summary. This is a pure alias -- no Phase 4 layout/formatting logic is
# changed, and no other column is renamed.
BUYING_GROUP_OUTPUT_COLUMN = "Buying Group"

EXCEPTION_COLUMNS = [
    "Customer",
    "Normalized Customer",
    "Selected Buying Group",
    "Rejected Buying Group",
    "Selected Source",
    "Rejected Source",
    "Status",
    "Reason",
]

AUDIT_COLUMNS = ["Metric", "Value"]


@dataclass(frozen=True)
class BuyingGroupLookupResult:
    """Result of the multi-source Buying Group enrichment."""

    dataframe: pd.DataFrame
    exceptions_df: pd.DataFrame
    audit_df: pd.DataFrame
    total_master_rows: int
    master_rows_after_merge: int
    unique_master_customers: int
    unique_source_customers: int
    exact_duplicate_source_rows_removed: int
    conflicting_customers: int
    lower_priority_disagreements: int
    matched_customers: int
    not_found_customers: int
    populated_rows: int
    blank_rows: int
    source_record_counts: dict = field(default_factory=dict)
    matches_by_source: dict = field(default_factory=dict)


def _empty_exceptions_df() -> pd.DataFrame:
    return pd.DataFrame(columns=EXCEPTION_COLUMNS)


def _empty_audit_df() -> pd.DataFrame:
    return pd.DataFrame(columns=AUDIT_COLUMNS)


def _clean_source_table(
    source_df: pd.DataFrame,
    customer_column: str,
    buying_group_column: str,
    display_name: str,
    priority: int,
) -> tuple[pd.DataFrame, int, list[dict]]:
    """Build a deduplicated, conflict-aware table for ONE source.

    Returns a per-source table with one row per normalized customer, the
    number of exact-duplicate rows removed, and any same-tier
    DUPLICATE_CONFLICT exception rows found within this single source.
    """
    working = source_df.copy()
    working["__customer_normalized__"] = working[customer_column].apply(normalize_text_key)
    working["__group_normalized__"] = working[buying_group_column].apply(normalize_text_key)
    working = working[[customer_column, buying_group_column, "__customer_normalized__", "__group_normalized__"]]

    # Rows with no usable customer key or no usable Buying Group value carry
    # no mapping information and are dropped before dedup/conflict analysis.
    working = working[working["__customer_normalized__"].notna() & working["__group_normalized__"].notna()]

    before_dedup = len(working)
    # Exact duplicates: identical normalized customer AND identical
    # normalized Buying Group. Safe to collapse -- same mapping restated.
    deduped = working.drop_duplicates(subset=["__customer_normalized__", "__group_normalized__"], keep="first")
    exact_duplicates_removed = before_dedup - len(deduped)

    exceptions: list[dict] = []
    rows: list[dict] = []

    for customer_normalized, group in deduped.groupby("__customer_normalized__", dropna=True):
        distinct_groups = group["__group_normalized__"].unique()
        observed_customers = sorted(set(group[customer_column].dropna().astype(str)))
        observed_groups = sorted(set(group[buying_group_column].dropna().astype(str)))
        customer_original = observed_customers[0] if observed_customers else ""

        if len(distinct_groups) > 1:
            # Same priority tier, multiple distinct values, no deterministic
            # rule available -> genuine conflict. Never guess, never pick
            # first/last, never invent a value.
            exceptions.append(
                {
                    "Customer": "; ".join(observed_customers),
                    "Normalized Customer": customer_normalized,
                    "Selected Buying Group": "",
                    "Rejected Buying Group": "; ".join(observed_groups),
                    "Selected Source": "",
                    "Rejected Source": display_name,
                    "Status": BUYING_GROUP_STATUS_DUPLICATE_CONFLICT,
                    "Reason": (
                        f"Customer maps to multiple different Buying Group values within the same "
                        f"priority tier ({display_name}, priority {priority}); no deterministic rule to choose"
                    ),
                }
            )
            rows.append(
                {
                    "__customer_normalized__": customer_normalized,
                    BUYING_GROUP_VALUE_COLUMN: pd.NA,
                    BUYING_GROUP_SOURCE_COLUMN: display_name,
                    "__status__": BUYING_GROUP_STATUS_DUPLICATE_CONFLICT,
                    "__priority__": priority,
                    "__customer_original__": customer_original,
                }
            )
        else:
            rows.append(
                {
                    "__customer_normalized__": customer_normalized,
                    BUYING_GROUP_VALUE_COLUMN: group[buying_group_column].dropna().iloc[0],
                    BUYING_GROUP_SOURCE_COLUMN: display_name,
                    "__status__": BUYING_GROUP_STATUS_MATCHED,
                    "__priority__": priority,
                    "__customer_original__": customer_original,
                }
            )

    table = pd.DataFrame(
        rows,
        columns=[
            "__customer_normalized__",
            BUYING_GROUP_VALUE_COLUMN,
            BUYING_GROUP_SOURCE_COLUMN,
            "__status__",
            "__priority__",
            "__customer_original__",
        ],
    )
    return table, exact_duplicates_removed, exceptions


def _resolve_by_priority(per_source_tables: list[pd.DataFrame]) -> tuple[pd.DataFrame, list[dict]]:
    """Collapse per-source tables into one row per normalized customer.

    The winning row for each customer is the one from the lowest ``priority``
    number (1 = highest priority). Any DIFFERENT Buying Group value supplied
    by a lower-priority source is recorded as a lower-priority disagreement
    exception -- it is a deterministic resolution, not a DUPLICATE_CONFLICT.
    """
    resolved_columns = [
        "__customer_normalized__",
        BUYING_GROUP_VALUE_COLUMN,
        BUYING_GROUP_SOURCE_COLUMN,
        "__status__",
    ]
    non_empty = [table for table in per_source_tables if not table.empty]
    if not non_empty:
        return pd.DataFrame(columns=resolved_columns), []

    combined = pd.concat(non_empty, ignore_index=True)
    combined["__group_normalized__"] = combined[BUYING_GROUP_VALUE_COLUMN].apply(normalize_text_key)

    resolved_rows: list[dict] = []
    disagreements: list[dict] = []

    for customer_normalized, group in combined.groupby("__customer_normalized__", dropna=True):
        group = group.sort_values("__priority__", kind="stable")
        winner = group.iloc[0]

        # Record any lower-priority source that supplied a DIFFERENT value.
        for _, other in group.iloc[1:].iterrows():
            if pd.isna(other["__group_normalized__"]) or pd.isna(winner["__group_normalized__"]):
                continue
            if other["__group_normalized__"] == winner["__group_normalized__"]:
                continue
            disagreements.append(
                {
                    "Customer": str(winner["__customer_original__"]),
                    "Normalized Customer": customer_normalized,
                    "Selected Buying Group": ""
                    if pd.isna(winner[BUYING_GROUP_VALUE_COLUMN])
                    else str(winner[BUYING_GROUP_VALUE_COLUMN]),
                    "Rejected Buying Group": ""
                    if pd.isna(other[BUYING_GROUP_VALUE_COLUMN])
                    else str(other[BUYING_GROUP_VALUE_COLUMN]),
                    "Selected Source": str(winner[BUYING_GROUP_SOURCE_COLUMN]),
                    "Rejected Source": str(other[BUYING_GROUP_SOURCE_COLUMN]),
                    "Status": BUYING_GROUP_STATUS_LOWER_PRIORITY_DISAGREEMENT,
                    "Reason": (
                        f"Resolved deterministically by source priority: "
                        f"{winner[BUYING_GROUP_SOURCE_COLUMN]} (priority {winner['__priority__']}) "
                        f"outranks {other[BUYING_GROUP_SOURCE_COLUMN]} (priority {other['__priority__']})"
                    ),
                }
            )

        resolved_rows.append(
            {
                "__customer_normalized__": customer_normalized,
                BUYING_GROUP_VALUE_COLUMN: winner[BUYING_GROUP_VALUE_COLUMN],
                BUYING_GROUP_SOURCE_COLUMN: winner[BUYING_GROUP_SOURCE_COLUMN],
                "__status__": winner["__status__"],
            }
        )

    return pd.DataFrame(resolved_rows, columns=resolved_columns), disagreements


def build_buying_group_lookup(
    master_df: pd.DataFrame,
    source_frames,
    *,
    master_customer_column: str,
    buying_group_sources: Sequence,
    logger,
) -> BuyingGroupLookupResult:
    """Enrich ``master_df`` with a Buying Group resolved across all sources.

    ``master_df``'s ``master_customer_column`` (e.g. "Sold-to party Name")
    and every source's own customer column are never modified; only
    temporary normalized keys are used for matching. The master row count is
    always preserved exactly.
    """
    total_master_rows = len(master_df)
    working = master_df.copy()

    if master_customer_column not in working.columns:
        logger.warning(
            "Buying Group lookup skipped: master column '%s' not found on master dataframe",
            master_customer_column,
        )
        working[BUYING_GROUP_VALUE_COLUMN] = pd.NA
        working[BUYING_GROUP_OUTPUT_COLUMN] = pd.NA
        working[BUYING_GROUP_SOURCE_COLUMN] = pd.NA
        working[BUYING_GROUP_STATUS_COLUMN] = BUYING_GROUP_STATUS_NOT_FOUND
        return BuyingGroupLookupResult(
            dataframe=working,
            exceptions_df=_empty_exceptions_df(),
            audit_df=_empty_audit_df(),
            total_master_rows=total_master_rows,
            master_rows_after_merge=len(working),
            unique_master_customers=0,
            unique_source_customers=0,
            exact_duplicate_source_rows_removed=0,
            conflicting_customers=0,
            lower_priority_disagreements=0,
            matched_customers=0,
            not_found_customers=total_master_rows,
            populated_rows=0,
            blank_rows=total_master_rows,
        )

    # --- Build the consolidated internal Buying Group master ---------------
    per_source_tables: list[pd.DataFrame] = []
    conflict_exceptions: list[dict] = []
    source_record_counts: dict[str, int] = {}
    total_exact_duplicates_removed = 0

    for source in sorted(buying_group_sources, key=lambda item: item.priority):
        source_df = source_frames.get(source.dataframe_key) if source_frames else None
        if (
            source_df is None
            or source_df.empty
            or source.customer_column not in source_df.columns
            or source.buying_group_column not in source_df.columns
        ):
            logger.warning(
                "Buying Group source '%s' (priority %s) unavailable: dataframe missing, empty, or "
                "missing required columns ('%s', '%s')",
                source.display_name,
                source.priority,
                source.customer_column,
                source.buying_group_column,
            )
            source_record_counts[source.display_name] = 0
            continue

        table, duplicates_removed, exceptions = _clean_source_table(
            source_df,
            source.customer_column,
            source.buying_group_column,
            source.display_name,
            source.priority,
        )
        per_source_tables.append(table)
        conflict_exceptions.extend(exceptions)
        total_exact_duplicates_removed += duplicates_removed
        source_record_counts[source.display_name] = len(source_df)

        logger.info(
            "Buying Group source loaded | source=%s | priority=%s | raw_rows=%s | unique_customers=%s | "
            "exact_duplicates_removed=%s | same_tier_conflicts=%s",
            source.display_name,
            source.priority,
            len(source_df),
            int(table["__customer_normalized__"].nunique()) if not table.empty else 0,
            duplicates_removed,
            len(exceptions),
        )

    lookup_table, disagreements = _resolve_by_priority(per_source_tables)

    # Invariant: the resolved table must map each normalized customer exactly
    # once, otherwise the left join below could multiply master rows.
    if not lookup_table.empty:
        assert lookup_table["__customer_normalized__"].is_unique, (
            "Internal invariant violated: the consolidated Buying Group lookup table must have a "
            "unique row per normalized customer"
        )

    # --- Join onto the master, preserving row count ------------------------
    working["__master_customer_normalized__"] = working[master_customer_column].apply(normalize_text_key)

    if lookup_table.empty:
        merged = working.copy()
        merged[BUYING_GROUP_VALUE_COLUMN] = pd.NA
        merged[BUYING_GROUP_SOURCE_COLUMN] = pd.NA
        merged["__status__"] = pd.NA
    else:
        merged = working.merge(
            lookup_table,
            left_on="__master_customer_normalized__",
            right_on="__customer_normalized__",
            how="left",
            suffixes=("", "__buying_group_source"),
        )

    master_rows_after_merge = len(merged)
    if master_rows_after_merge != total_master_rows:
        raise ValueError(
            f"Buying Group merge altered master row count: before={total_master_rows} "
            f"after={master_rows_after_merge}. This indicates a non-unique lookup key slipped through "
            "deduplication/priority resolution."
        )

    status = merged["__status__"]
    lookup_status = status.where(status.notna(), BUYING_GROUP_STATUS_NOT_FOUND)
    merged[BUYING_GROUP_STATUS_COLUMN] = lookup_status
    # Source lineage is only meaningful for rows that actually matched.
    merged[BUYING_GROUP_SOURCE_COLUMN] = merged[BUYING_GROUP_SOURCE_COLUMN].where(
        lookup_status == BUYING_GROUP_STATUS_MATCHED, pd.NA
    )
    merged = merged.drop(
        columns=["__master_customer_normalized__", "__customer_normalized__", "__status__"],
        errors="ignore",
    )
    # Publish the business-facing alias consumed by Phase 4 / the POB
    # Summary layout. Identical resolved value, no separate logic.
    merged[BUYING_GROUP_OUTPUT_COLUMN] = merged[BUYING_GROUP_VALUE_COLUMN]

    # --- Statistics --------------------------------------------------------
    populated_rows = int(merged[BUYING_GROUP_VALUE_COLUMN].notna().sum())
    blank_rows = total_master_rows - populated_rows
    matched_customers = int((lookup_status == BUYING_GROUP_STATUS_MATCHED).sum())
    not_found_customers = int((lookup_status == BUYING_GROUP_STATUS_NOT_FOUND).sum())
    conflicting_rows_in_master = int((lookup_status == BUYING_GROUP_STATUS_DUPLICATE_CONFLICT).sum())

    unique_master_customers = int(working[master_customer_column].apply(normalize_text_key).dropna().nunique())
    unique_source_customers = int(lookup_table["__customer_normalized__"].nunique()) if not lookup_table.empty else 0
    conflicting_customers = (
        int((lookup_table["__status__"] == BUYING_GROUP_STATUS_DUPLICATE_CONFLICT).sum())
        if not lookup_table.empty
        else 0
    )

    matched_mask = lookup_status == BUYING_GROUP_STATUS_MATCHED
    matches_by_source = (
        merged.loc[matched_mask, BUYING_GROUP_SOURCE_COLUMN].value_counts().to_dict() if matched_mask.any() else {}
    )

    # --- NOT_FOUND exceptions (only after ALL sources were checked) --------
    not_found_names = sorted(
        set(merged.loc[lookup_status == BUYING_GROUP_STATUS_NOT_FOUND, master_customer_column].dropna().astype(str))
    )
    not_found_exceptions = [
        {
            "Customer": customer,
            "Normalized Customer": normalize_text_key(customer),
            "Selected Buying Group": "",
            "Rejected Buying Group": "",
            "Selected Source": "",
            "Rejected Source": "",
            "Status": BUYING_GROUP_STATUS_NOT_FOUND,
            "Reason": "Customer not present in ANY configured authoritative Buying Group source",
        }
        for customer in not_found_names
    ]

    exceptions_df = pd.DataFrame(
        conflict_exceptions + disagreements + not_found_exceptions,
        columns=EXCEPTION_COLUMNS,
    )

    # --- Audit sheet -------------------------------------------------------
    audit_rows: list[dict] = [
        {"Metric": "Total master rows", "Value": total_master_rows},
        {"Metric": "Master rows after merge", "Value": master_rows_after_merge},
        {"Metric": "Unique master customers", "Value": unique_master_customers},
        {"Metric": "Unique consolidated source customers", "Value": unique_source_customers},
        {"Metric": "Exact duplicate source rows removed", "Value": total_exact_duplicates_removed},
        {"Metric": "Matched rows", "Value": matched_customers},
        {"Metric": "NOT_FOUND rows", "Value": not_found_customers},
        {"Metric": "DUPLICATE_CONFLICT rows", "Value": conflicting_rows_in_master},
        {"Metric": "Same-priority conflicting customers", "Value": conflicting_customers},
        {"Metric": "Lower-priority disagreements", "Value": len(disagreements)},
        {"Metric": "Populated Buying Group rows", "Value": populated_rows},
        {"Metric": "Blank Buying Group rows", "Value": blank_rows},
    ]
    for source in sorted(buying_group_sources, key=lambda item: item.priority):
        audit_rows.append(
            {
                "Metric": f"Source record count - {source.display_name} (priority {source.priority})",
                "Value": source_record_counts.get(source.display_name, 0),
            }
        )
        audit_rows.append(
            {
                "Metric": f"Master rows matched from {source.display_name}",
                "Value": int(matches_by_source.get(source.display_name, 0)),
            }
        )
    # Final source selected per customer, for full lineage auditability.
    if matched_mask.any():
        per_customer = (
            merged.loc[
                matched_mask,
                [master_customer_column, BUYING_GROUP_VALUE_COLUMN, BUYING_GROUP_SOURCE_COLUMN],
            ]
            .drop_duplicates()
            .sort_values(master_customer_column)
        )
        for _, row in per_customer.iterrows():
            audit_rows.append(
                {
                    "Metric": f"Final source for customer '{row[master_customer_column]}'",
                    "Value": f"{row[BUYING_GROUP_SOURCE_COLUMN]} -> {row[BUYING_GROUP_VALUE_COLUMN]}",
                }
            )

    audit_df = pd.DataFrame(audit_rows, columns=AUDIT_COLUMNS)

    logger.info(
        "Buying Group multi-source lookup | total_master_rows=%s | rows_after_merge=%s | "
        "unique_master_customers=%s | unique_source_customers=%s | exact_duplicates_removed=%s | "
        "same_priority_conflicts=%s | lower_priority_disagreements=%s | matched_rows=%s | "
        "not_found_rows=%s | duplicate_conflict_rows=%s | populated_rows=%s | blank_rows=%s | "
        "matches_by_source=%s",
        total_master_rows,
        master_rows_after_merge,
        unique_master_customers,
        unique_source_customers,
        total_exact_duplicates_removed,
        conflicting_customers,
        len(disagreements),
        matched_customers,
        not_found_customers,
        conflicting_rows_in_master,
        populated_rows,
        blank_rows,
        matches_by_source,
    )

    return BuyingGroupLookupResult(
        dataframe=merged,
        exceptions_df=exceptions_df,
        audit_df=audit_df,
        total_master_rows=total_master_rows,
        master_rows_after_merge=master_rows_after_merge,
        unique_master_customers=unique_master_customers,
        unique_source_customers=unique_source_customers,
        exact_duplicate_source_rows_removed=total_exact_duplicates_removed,
        conflicting_customers=conflicting_customers,
        lower_priority_disagreements=len(disagreements),
        matched_customers=matched_customers,
        not_found_customers=not_found_customers,
        populated_rows=populated_rows,
        blank_rows=blank_rows,
        source_record_counts=source_record_counts,
        matches_by_source=matches_by_source,
    )
