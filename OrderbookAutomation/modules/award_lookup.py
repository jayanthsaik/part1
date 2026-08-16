from __future__ import annotations

"""Dedicated, auditable Award Type lookup.

Replaces the generic SOURCE_SPECS-driven merge for the Awards source with a
purpose-built, deterministic lookup operating at the grain the source data
actually proves to be correct.

Grain (established from Awards.xlsx itself, not assumed):

- ``Lookup`` in Awards.xlsx equals ``normalize_ndc_key(NDC) +
  normalize_text_key(Sold to party)`` for 129/129 rows, i.e. Award Type is
  recorded at CUSTOMER + NDC grain.
- 19 of 80 distinct sold-to-parties carry MORE THAN ONE distinct Award Type
  across their NDCs, so customer-only matching is provably WRONG and is
  therefore deliberately NOT offered as a strategy here.
- 0 of 129 Customer+NDC groups disagree, so Customer+NDC is a clean grain.

Strategies, in order:

1. PRIMARY  -- master canonical ``Lookup`` -> Awards ``Lookup``
   (full Customer + NDC grain).
2. FALLBACK -- normalized master ``NDC Code`` -> Awards ``NDC``
   (product-level). Only applied to rows the primary strategy could not
   resolve, and only when the NDC maps to a single unambiguous Award Type;
   an NDC carrying multiple distinct Award Types across customers is a
   DUPLICATE_CONFLICT and is left blank rather than guessed.

Guarantees:

- The exact master row count is always preserved.
- Original business columns are never modified; only temporary normalized
  keys are derived.
- Values are never invented. A row is only NOT_FOUND after both strategies
  have been attempted.
- ``Award Lookup Status`` and ``Award Match Strategy`` are internal
  diagnostic columns and are not part of the POB output schema.
"""

from dataclasses import dataclass, field

import pandas as pd

from modules.utils import normalize_ndc_key, normalize_text_key

AWARD_STATUS_MATCHED = "MATCHED"
AWARD_STATUS_NOT_FOUND = "NOT_FOUND"
AWARD_STATUS_DUPLICATE_CONFLICT = "DUPLICATE_CONFLICT"

AWARD_STATUS_COLUMN = "Award Lookup Status"
AWARD_STRATEGY_COLUMN = "Award Match Strategy"
AWARD_VALUE_COLUMN = "Award Type"

AWARD_STRATEGY_LOOKUP = "Lookup (Customer+NDC)"
AWARD_STRATEGY_NDC = "NDC (product-level fallback)"

AWARD_EXCEPTION_COLUMNS = [
    "Customer",
    "NDC",
    "Lookup",
    "Award Type",
    "Match Strategy",
    "Status",
    "Reason",
]


@dataclass(frozen=True)
class AwardLookupResult:
    dataframe: pd.DataFrame
    exceptions_df: pd.DataFrame
    total_master_rows: int
    master_rows_after_merge: int
    matched_rows: int
    matched_by_lookup: int
    matched_by_ndc: int
    not_found_rows: int
    duplicate_conflict_rows: int
    populated_rows: int
    blank_rows: int
    source_rows: int = 0
    conflicting_ndcs: int = 0
    exact_duplicate_source_rows_removed: int = 0
    details: dict = field(default_factory=dict)


def _empty_exceptions_df() -> pd.DataFrame:
    return pd.DataFrame(columns=AWARD_EXCEPTION_COLUMNS)


def _blank_result(master_df: pd.DataFrame, reason: str, logger) -> AwardLookupResult:
    logger.warning("Award lookup skipped: %s", reason)
    working = master_df.copy()
    working[AWARD_VALUE_COLUMN] = pd.NA
    working[AWARD_STATUS_COLUMN] = AWARD_STATUS_NOT_FOUND
    working[AWARD_STRATEGY_COLUMN] = pd.NA
    total = len(master_df)
    return AwardLookupResult(
        dataframe=working,
        exceptions_df=_empty_exceptions_df(),
        total_master_rows=total,
        master_rows_after_merge=total,
        matched_rows=0,
        matched_by_lookup=0,
        matched_by_ndc=0,
        not_found_rows=total,
        duplicate_conflict_rows=0,
        populated_rows=0,
        blank_rows=total,
    )


def _build_lookup_table(
    awards_df: pd.DataFrame,
    source_lookup_column: str,
    award_column: str,
) -> tuple[pd.DataFrame, int, list[dict]]:
    """Build a unique normalized-Lookup -> Award Type table (Customer+NDC grain)."""
    working = awards_df.copy()
    working["__key__"] = working[source_lookup_column].apply(normalize_text_key)
    working["__award_normalized__"] = working[award_column].apply(normalize_text_key)
    working = working[working["__key__"].notna() & working["__award_normalized__"].notna()]

    before = len(working)
    deduped = working.drop_duplicates(subset=["__key__", "__award_normalized__"], keep="first")
    duplicates_removed = before - len(deduped)

    rows: list[dict] = []
    exceptions: list[dict] = []
    for key, group in deduped.groupby("__key__", dropna=True):
        distinct = group["__award_normalized__"].unique()
        if len(distinct) > 1:
            # Same Customer+NDC with genuinely different Award Types and no
            # deterministic rule to choose between them -> never guess.
            exceptions.append(
                {
                    "Customer": "",
                    "NDC": "",
                    "Lookup": key,
                    "Award Type": "; ".join(sorted(set(group[award_column].dropna().astype(str)))),
                    "Match Strategy": AWARD_STRATEGY_LOOKUP,
                    "Status": AWARD_STATUS_DUPLICATE_CONFLICT,
                    "Reason": "Same Lookup (Customer+NDC) maps to multiple distinct Award Type values in Awards source",
                }
            )
            rows.append({"__key__": key, "__award__": pd.NA, "__status__": AWARD_STATUS_DUPLICATE_CONFLICT})
        else:
            rows.append(
                {
                    "__key__": key,
                    "__award__": group[award_column].dropna().iloc[0],
                    "__status__": AWARD_STATUS_MATCHED,
                }
            )

    table = pd.DataFrame(rows, columns=["__key__", "__award__", "__status__"])
    return table, duplicates_removed, exceptions


def _build_ndc_table(
    awards_df: pd.DataFrame,
    source_ndc_column: str,
    award_column: str,
) -> tuple[pd.DataFrame, list[dict]]:
    """Build a normalized-NDC -> Award Type table for the product-level fallback.

    An NDC that carries more than one distinct Award Type across customers is
    genuinely ambiguous at product level and is recorded as a
    DUPLICATE_CONFLICT rather than resolved arbitrarily.
    """
    working = awards_df.copy()
    working["__key__"] = working[source_ndc_column].apply(normalize_ndc_key)
    working["__award_normalized__"] = working[award_column].apply(normalize_text_key)
    working = working[working["__key__"].notna() & working["__award_normalized__"].notna()]

    rows: list[dict] = []
    exceptions: list[dict] = []
    for key, group in working.groupby("__key__", dropna=True):
        distinct = group["__award_normalized__"].unique()
        if len(distinct) > 1:
            exceptions.append(
                {
                    "Customer": "",
                    "NDC": key,
                    "Lookup": "",
                    "Award Type": "; ".join(sorted(set(group[award_column].dropna().astype(str)))),
                    "Match Strategy": AWARD_STRATEGY_NDC,
                    "Status": AWARD_STATUS_DUPLICATE_CONFLICT,
                    "Reason": "NDC maps to multiple distinct Award Type values across customers; ambiguous at product level",
                }
            )
            rows.append({"__key__": key, "__award__": pd.NA, "__status__": AWARD_STATUS_DUPLICATE_CONFLICT})
        else:
            rows.append(
                {
                    "__key__": key,
                    "__award__": group[award_column].dropna().iloc[0],
                    "__status__": AWARD_STATUS_MATCHED,
                }
            )

    table = pd.DataFrame(rows, columns=["__key__", "__award__", "__status__"])
    return table, exceptions


def build_award_lookup(
    master_df: pd.DataFrame,
    awards_df: pd.DataFrame | None,
    *,
    master_lookup_column: str,
    master_ndc_column: str,
    master_customer_column: str,
    source_lookup_column: str,
    source_ndc_column: str,
    award_column: str,
    logger,
) -> AwardLookupResult:
    """Attach Award Type to ``master_df`` at Customer+NDC grain, with an
    NDC-level fallback. Never multiplies rows, never invents values."""
    total_master_rows = len(master_df)

    if awards_df is None or awards_df.empty:
        return _blank_result(master_df, "Awards source dataframe missing or empty", logger)
    if award_column not in awards_df.columns:
        return _blank_result(master_df, f"Awards source missing '{award_column}' column", logger)

    working = master_df.copy()
    # Start from a clean slate: any Award Type accidentally introduced by an
    # unrelated upstream merge is not authoritative.
    working[AWARD_VALUE_COLUMN] = pd.NA
    working[AWARD_STATUS_COLUMN] = AWARD_STATUS_NOT_FOUND
    working[AWARD_STRATEGY_COLUMN] = pd.NA

    exceptions: list[dict] = []
    duplicates_removed = 0
    conflicting_ndcs = 0

    # ---- PRIMARY: Lookup (Customer + NDC grain) --------------------------
    matched_by_lookup = 0
    if master_lookup_column in working.columns and source_lookup_column in awards_df.columns:
        table, duplicates_removed, lookup_exceptions = _build_lookup_table(
            awards_df, source_lookup_column, award_column
        )
        exceptions.extend(lookup_exceptions)
        if not table.empty:
            assert table["__key__"].is_unique, "Award Lookup table must be unique per normalized Lookup"
            mapping = table.set_index("__key__")
            keys = working[master_lookup_column].apply(normalize_text_key)
            awards = keys.map(mapping["__award__"])
            statuses = keys.map(mapping["__status__"])

            hit = statuses.notna()
            working.loc[hit, AWARD_VALUE_COLUMN] = awards[hit]
            working.loc[hit, AWARD_STATUS_COLUMN] = statuses[hit]
            working.loc[hit, AWARD_STRATEGY_COLUMN] = AWARD_STRATEGY_LOOKUP
            matched_by_lookup = int((statuses == AWARD_STATUS_MATCHED).sum())
    else:
        logger.warning(
            "Award primary strategy unavailable: master '%s' or Awards '%s' column not found",
            master_lookup_column,
            source_lookup_column,
        )

    # ---- FALLBACK: normalized NDC (product level) ------------------------
    # Applied ONLY to rows still unresolved by the primary strategy.
    matched_by_ndc = 0
    unresolved = working[AWARD_STATUS_COLUMN] == AWARD_STATUS_NOT_FOUND
    if unresolved.any() and master_ndc_column in working.columns and source_ndc_column in awards_df.columns:
        ndc_table, ndc_exceptions = _build_ndc_table(awards_df, source_ndc_column, award_column)
        exceptions.extend(ndc_exceptions)
        conflicting_ndcs = len(ndc_exceptions)
        if not ndc_table.empty:
            assert ndc_table["__key__"].is_unique, "Award NDC table must be unique per normalized NDC"
            mapping = ndc_table.set_index("__key__")
            keys = working.loc[unresolved, master_ndc_column].apply(normalize_ndc_key)
            awards = keys.map(mapping["__award__"])
            statuses = keys.map(mapping["__status__"])

            hit = statuses.notna()
            hit_index = keys.index[hit]
            working.loc[hit_index, AWARD_VALUE_COLUMN] = awards[hit]
            working.loc[hit_index, AWARD_STATUS_COLUMN] = statuses[hit]
            working.loc[hit_index, AWARD_STRATEGY_COLUMN] = AWARD_STRATEGY_NDC
            matched_by_ndc = int((statuses == AWARD_STATUS_MATCHED).sum())

    # ---- Row count invariant --------------------------------------------
    master_rows_after_merge = len(working)
    if master_rows_after_merge != total_master_rows:
        raise ValueError(
            f"Award lookup altered master row count: before={total_master_rows} after={master_rows_after_merge}"
        )

    status_series = working[AWARD_STATUS_COLUMN]
    matched_rows = int((status_series == AWARD_STATUS_MATCHED).sum())
    not_found_rows = int((status_series == AWARD_STATUS_NOT_FOUND).sum())
    duplicate_conflict_rows = int((status_series == AWARD_STATUS_DUPLICATE_CONFLICT).sum())
    populated_rows = int(working[AWARD_VALUE_COLUMN].notna().sum())
    blank_rows = total_master_rows - populated_rows

    # ---- NOT_FOUND exceptions (only after BOTH strategies attempted) -----
    not_found_mask = status_series == AWARD_STATUS_NOT_FOUND
    if not_found_mask.any():
        columns = [
            column
            for column in (master_customer_column, master_ndc_column, master_lookup_column)
            if column in working.columns
        ]
        distinct = working.loc[not_found_mask, columns].drop_duplicates()
        for _, row in distinct.iterrows():
            exceptions.append(
                {
                    "Customer": row.get(master_customer_column, ""),
                    "NDC": row.get(master_ndc_column, ""),
                    "Lookup": row.get(master_lookup_column, ""),
                    "Award Type": "",
                    "Match Strategy": "",
                    "Status": AWARD_STATUS_NOT_FOUND,
                    "Reason": "No Award record found by Lookup (Customer+NDC) or by NDC in the Awards source",
                }
            )

    exceptions_df = pd.DataFrame(exceptions, columns=AWARD_EXCEPTION_COLUMNS)

    logger.info(
        "Award lookup stats | source_rows=%s | total_master_rows=%s | rows_after_merge=%s | "
        "matched=%s (lookup=%s, ndc=%s) | not_found=%s | duplicate_conflict=%s | "
        "populated=%s | blank=%s | exact_duplicate_source_rows_removed=%s | conflicting_ndcs=%s",
        len(awards_df),
        total_master_rows,
        master_rows_after_merge,
        matched_rows,
        matched_by_lookup,
        matched_by_ndc,
        not_found_rows,
        duplicate_conflict_rows,
        populated_rows,
        blank_rows,
        duplicates_removed,
        conflicting_ndcs,
    )

    return AwardLookupResult(
        dataframe=working,
        exceptions_df=exceptions_df,
        total_master_rows=total_master_rows,
        master_rows_after_merge=master_rows_after_merge,
        matched_rows=matched_rows,
        matched_by_lookup=matched_by_lookup,
        matched_by_ndc=matched_by_ndc,
        not_found_rows=not_found_rows,
        duplicate_conflict_rows=duplicate_conflict_rows,
        populated_rows=populated_rows,
        blank_rows=blank_rows,
        source_rows=len(awards_df),
        conflicting_ndcs=conflicting_ndcs,
        exact_duplicate_source_rows_removed=duplicates_removed,
    )
