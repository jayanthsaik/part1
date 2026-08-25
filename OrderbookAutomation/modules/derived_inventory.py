from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pandas as pd

from config import INVENTORY_COLUMNS, OPEN_ORDER_COLUMNS, Phase2Config
from modules.utils import clean_string_value, coerce_numeric_column, is_blank_hold_code, normalize_identifier_key


@dataclass(frozen=True)
class DerivedInventoryResult:
    """Derived UPS inventory dataset and supporting counters."""

    dataframe: pd.DataFrame
    inventory_rows: int
    allocated_rows: int
    unique_ndcs: int
    missing_inventory: int
    missing_allocations: int
    total_inventory_rows: int = 0
    blank_hold_code_rows: int = 0
    excluded_hold_code_rows: int = 0
    unique_ndcs_before_filter: int = 0
    unique_ndcs_after_filter: int = 0
    inventory_qty_before_filter: float = 0.0
    inventory_qty_after_filter: float = 0.0


def build_ups_inventory(
    inventory_df: pd.DataFrame,
    open_orders_df: pd.DataFrame,
    phase2_config: Phase2Config,
    logger,
    upload_adjustments_df: pd.DataFrame | None = None,
) -> DerivedInventoryResult:
    """Build UPS inventory by netting filtered open order allocations against inventory."""
    _validate_required_columns(
        inventory_df,
        [INVENTORY_COLUMNS["ndc"], INVENTORY_COLUMNS["inventory"]],
        "inventory",
    )
    _validate_required_columns(
        open_orders_df,
        [OPEN_ORDER_COLUMNS["sku"], OPEN_ORDER_COLUMNS["total"], OPEN_ORDER_COLUMNS["pickticket_status"]],
        "open_order_summary",
    )

    inventory_working = inventory_df.copy()
    open_orders_working = open_orders_df.copy()

    inventory_ndc_col = INVENTORY_COLUMNS["ndc"]
    inventory_qty_col = INVENTORY_COLUMNS["inventory"]
    open_order_sku_col = OPEN_ORDER_COLUMNS["sku"]
    open_order_total_col = OPEN_ORDER_COLUMNS["total"]
    open_order_status_col = OPEN_ORDER_COLUMNS["pickticket_status"]

    inventory_working[inventory_ndc_col] = inventory_working[inventory_ndc_col].apply(normalize_identifier_key)
    inventory_working[inventory_qty_col] = coerce_numeric_column(inventory_working[inventory_qty_col])

    duplicate_inventory_ndc = int(inventory_working[inventory_ndc_col].dropna().duplicated().sum())
    if duplicate_inventory_ndc > 0:
        logger.warning("Duplicate inventory NDC values detected: %s", duplicate_inventory_ndc)

    # ---- Hold Codes eligibility filter (BUSINESS RULE) --------------------
    # ONLY Daily Inventory rows with a BLANK Hold Codes value are eligible
    # to contribute to the UPS Inventory calculation. This filter is applied
    # here, before the inventory summary/netting logic, and does NOT touch
    # the Orderbook or Open Order Summary in any way. The original Hold
    # Codes column is never modified; only a temporary boolean mask is used.
    total_inventory_rows = len(inventory_working)
    unique_ndcs_before_filter = int(inventory_working[inventory_ndc_col].dropna().nunique())
    inventory_qty_before_filter = float(inventory_working[inventory_qty_col].fillna(0).sum())

    hold_codes_col = INVENTORY_COLUMNS.get("hold_codes")
    if hold_codes_col and hold_codes_col in inventory_working.columns:
        blank_hold_code_mask = inventory_working[hold_codes_col].apply(is_blank_hold_code)
        blank_hold_code_rows = int(blank_hold_code_mask.sum())
        excluded_hold_code_rows = total_inventory_rows - blank_hold_code_rows
        inventory_working = inventory_working.loc[blank_hold_code_mask].copy()
    else:
        logger.warning(
            "Inventory source missing '%s' column; Hold Codes filter skipped, all rows treated as eligible",
            hold_codes_col,
        )
        blank_hold_code_rows = total_inventory_rows
        excluded_hold_code_rows = 0

    unique_ndcs_after_filter = int(inventory_working[inventory_ndc_col].dropna().nunique())
    inventory_qty_after_filter = float(inventory_working[inventory_qty_col].fillna(0).sum())

    logger.info(
        "UPS Inventory Hold Code Filter | total_inventory_rows=%s | blank_hold_codes=%s | "
        "excluded_hold_codes=%s | unique_ndcs_before=%s | unique_ndcs_after=%s | "
        "inventory_before_filter=%s | inventory_after_filter=%s",
        total_inventory_rows,
        blank_hold_code_rows,
        excluded_hold_code_rows,
        unique_ndcs_before_filter,
        unique_ndcs_after_filter,
        inventory_qty_before_filter,
        inventory_qty_after_filter,
    )

    # ---- Pickticket Status eligibility filter (BUSINESS RULE) -------------
    # Only open order rows whose Pickticket Status is one of the configured
    # INCLUDED statuses consume inventory:
    #   In Distribution, In Picking,
    #   Ready for Pickroot Creation, Ready for Wave Creation
    # Anything else (e.g. Pick Completed, Loaded, or any new/unknown status)
    # is ignored. Comparison is case-insensitive and whitespace-tolerant.
    # If no allow-list is configured, fall back to the legacy exclusion list.
    included_statuses = {
        normalized
        for normalized in (
            " ".join(str(status).split()).upper()
            for status in getattr(phase2_config, "open_order_included_statuses", ()) or ()
        )
        if normalized
    }
    normalized_status = open_orders_working[open_order_status_col].apply(
        lambda value: " ".join((clean_string_value(value) or "").split()).upper()
    )

    if included_statuses:
        status_mask = normalized_status.isin(included_statuses)
        logger.info(
            "Open order Pickticket Status filter (allow-list) | included=%s | rows_in=%s | rows_kept=%s | rows_dropped=%s",
            sorted(included_statuses),
            len(open_orders_working),
            int(status_mask.sum()),
            int((~status_mask).sum()),
        )
        unmatched = sorted(set(normalized_status[~status_mask].unique()) - included_statuses)
        if unmatched:
            logger.info("Open order statuses excluded from UPS netting: %s", unmatched)
    else:
        excluded_statuses = {
            " ".join(str(status).split()).upper()
            for status in phase2_config.open_order_excluded_statuses
        }
        status_mask = ~normalized_status.isin(excluded_statuses)
        logger.info(
            "Open order Pickticket Status filter (legacy exclusion list) | excluded=%s | rows_kept=%s",
            sorted(excluded_statuses),
            int(status_mask.sum()),
        )

    filtered_open_orders = open_orders_working.loc[status_mask].copy()

    missing_sku_mask = filtered_open_orders[open_order_sku_col].isna() | (
        filtered_open_orders[open_order_sku_col].astype("string").str.strip() == ""
    )
    missing_sku_count = int(missing_sku_mask.sum())
    if missing_sku_count > 0:
        logger.warning("Missing SKU values in open order summary: %s", missing_sku_count)

    filtered_open_orders["__derived_ndc__"] = filtered_open_orders[open_order_sku_col].apply(
        lambda value: sku_to_ndc(value, phase2_config, logger)
    )
    invalid_sku_count = int(filtered_open_orders[open_order_sku_col].notna().sum() - filtered_open_orders["__derived_ndc__"].notna().sum())
    if invalid_sku_count > 0:
        logger.warning("Invalid SKU values that could not be converted to NDC: %s", invalid_sku_count)

    filtered_open_orders[open_order_total_col] = coerce_numeric_column(filtered_open_orders[open_order_total_col]).fillna(0)
    allocation_summary = (
        filtered_open_orders.dropna(subset=["__derived_ndc__"])
        .groupby("__derived_ndc__", dropna=False)[open_order_total_col]
        .sum()
        .rename("Total")
        .reset_index()
        .rename(columns={"__derived_ndc__": "NDC"})
    )

    inventory_summary = (
        inventory_working.dropna(subset=[inventory_ndc_col])
        .groupby(inventory_ndc_col, dropna=False)[inventory_qty_col]
        .sum()
        .rename("Inventory")
        .reset_index()
        .rename(columns={inventory_ndc_col: "NDC"})
    )

    missing_inventory_keys = sorted(set(allocation_summary["NDC"].dropna()) - set(inventory_summary["NDC"].dropna()))
    if missing_inventory_keys:
        logger.warning("Missing inventory for allocated NDC values: %s", len(missing_inventory_keys))

    derived = inventory_summary.merge(allocation_summary, on="NDC", how="outer")
    # join optional upload adjustments (aggregated uploaded Sales Order Qty by NDC)
    if upload_adjustments_df is not None and not upload_adjustments_df.empty:
        derived = derived.merge(upload_adjustments_df, on="NDC", how="left")
        derived["Upload_Qty"] = coerce_numeric_column(derived.get("Upload_Qty", pd.Series(dtype="float"))).fillna(0)
        logger.info("Applying upload adjustments to UPS Inventory for %d NDCs", int(derived["NDC"].nunique(dropna=True)))
    else:
        derived["Upload_Qty"] = 0

    derived["Inventory"] = coerce_numeric_column(derived["Inventory"]).fillna(0)
    derived["Total"] = coerce_numeric_column(derived["Total"]).fillna(0)
    # BUSINESS RULE: UPS Inventory is Inventory - Total - Upload_Qty, floored at 0.
    # The subtraction is performed before clipping so shortages are auditable in the Inventory/Total/Upload_Qty columns.
    derived["UPS Inventory"] = (derived["Inventory"] - derived["Total"] - derived["Upload_Qty"]).clip(lower=0)
    derived = derived[["NDC", "Inventory", "Total", "UPS Inventory"]]

    missing_allocations = int((derived["Total"] == 0).sum())
    logger.info(
        "Derived inventory stats | inventory_rows=%s | allocated_rows=%s | unique_ndcs=%s | missing_inventory=%s | missing_allocations=%s",
        len(inventory_summary),
        len(allocation_summary),
        int(derived["NDC"].nunique(dropna=True)),
        len(missing_inventory_keys),
        missing_allocations,
    )

    return DerivedInventoryResult(
        dataframe=derived,
        inventory_rows=len(inventory_summary),
        allocated_rows=len(allocation_summary),
        unique_ndcs=int(derived["NDC"].nunique(dropna=True)),
        missing_inventory=len(missing_inventory_keys),
        missing_allocations=missing_allocations,
        total_inventory_rows=total_inventory_rows,
        blank_hold_code_rows=blank_hold_code_rows,
        excluded_hold_code_rows=excluded_hold_code_rows,
        unique_ndcs_before_filter=unique_ndcs_before_filter,
        unique_ndcs_after_filter=unique_ndcs_after_filter,
        inventory_qty_before_filter=inventory_qty_before_filter,
        inventory_qty_after_filter=inventory_qty_after_filter,
    )


def sku_to_ndc(value: object, phase2_config: Phase2Config, logger) -> str | None:
    """Convert a SKU value into a normalized NDC using configurable segmentation rules.

    A warehouse SKU (e.g. "64380-161-01") is split on the configured delimiter
    and each segment is validated against ``sku_segment_widths``. Because the
    business NDC join key is the 11-digit 5-4-2 form, each validated segment is
    then LEFT ZERO-PADDED to the corresponding ``ndc_segment_widths`` entry
    before the segments are concatenated. Without this padding a SKU would
    produce a 10-digit key ("6438016101") that can never match the inventory
    NDC ("64380016101"), silently leaving open orders unnetted.
    """
    cleaned = clean_string_value(value)
    if cleaned is None:
        return None

    delimiter = phase2_config.sku_delimiter
    segments = cleaned.split(delimiter) if delimiter else [cleaned]
    expected_lengths = tuple(int(width) for width in phase2_config.sku_segment_widths)
    target_lengths = tuple(int(width) for width in phase2_config.ndc_segment_widths)

    if len(segments) != len(expected_lengths):
        logger.warning("Invalid SKU format encountered: %s", cleaned)
        return None

    if len(target_lengths) != len(expected_lengths):
        raise ValueError(
            "Phase2Config.ndc_segment_widths must define one target width per sku_segment_widths entry"
        )

    normalized_segments: list[str] = []
    for segment, expected_length, target_length in zip(segments, expected_lengths, target_lengths, strict=True):
        segment_value = normalize_identifier_key(segment)
        if segment_value is None or not segment_value.isdigit() or len(segment_value) != expected_length:
            logger.warning("Invalid SKU segment encountered: %s", cleaned)
            return None
        normalized_segments.append(segment_value.zfill(target_length))

    return "".join(normalized_segments)


def _validate_required_columns(df: pd.DataFrame, required_columns: Sequence[str], dataset_name: str) -> None:
    """Raise when a required dataset is missing mandatory business columns."""
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"{dataset_name} dataframe is missing required columns: {', '.join(missing)}")