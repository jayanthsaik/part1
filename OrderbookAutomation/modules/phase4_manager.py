from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd
from openpyxl import Workbook

from modules.business_rules import apply_business_rules
from modules.final_orderbook_builder import enrich_master_with_phase2_and_cip, merge_historical_sales
from modules.historical_sales import build_historical_sales, determine_reporting_period
from modules.report_formatter import (
    apply_business_rule_formatting,
    apply_low_ups_inventory_formatting,
    apply_summary_action_formatting,
    save_workbook,
    write_dataframe_sheet,
)
from modules.sales_summary_builder import SUMMARY_ACTION_FLAG_COLUMN, build_sales_summary_aggregation
from modules.utils import normalize_ndc_key, normalize_text_key

# Final Orderbook sheet column order/headers, matching the authoritative
# reference workbook (sampo.xlsx) exactly (order/item grain -- one row per
# Sales Order No. + Item No.). Internal processing/enrichment columns
# (MOQ_Issue, Controlled_Product, Price_Issue, Price_Difference,
# Low_UPS_Inventory, SC Comments, Buying Group, Award Type, historical month
# columns, temporary lookup fields, etc.) must never leak into this sheet.
#
# Some reference headers differ from the internal working-column names used
# during Phase 1-4 processing (including embedded line breaks, e.g.
# "Matl.\nCode" and "Total Stock \nIn-hand"); this mapping renames FOR
# DISPLAY ONLY when writing the final Orderbook sheet. The internal working
# dataframe and all upstream business logic are untouched.
ORDERBOOK_COLUMN_RENAMES: dict[str, str] = {
    "Matl.Code": "Matl.\nCode",
    "Total Stock In-hand": "Total Stock \nIn-hand",
    "PackSize(MOQ)": "Pack Size (MOQ)",
    "PO number": "PO Number",
    "PO date": "PO Date",
}

# Exact reference headers (including embedded line breaks), in exact
# reference order, for the final client-facing Orderbook sheet, per
# sampo.xlsx.
ORDERBOOK_REFERENCE_COLUMNS: tuple[str, ...] = (
    "Sales Order No.",
    "Item No.",
    "Lookup",
    "Matl.\nCode",
    "NDC Code",
    "Material Description",
    "Total Stock \nIn-hand",
    "UPS Inventory",
    "Pack Size (MOQ)",
    "Sales Order Qty",
    "Sales Qty MTD",
    "Forecast Qty",
    "Sold-to party",
    "Sold-to party Name",
    "Action",
    "S.O. Type",
    "Unit Price",
    "Sales Value (FC)",
    "WAC/BG price in EDI",
    "PO Number",
    "PO Date",
    "Ship-to party",
    "Ship-to party Name",
    "Street",
    "City",
    "Region",
    "Postal Code",
    "Country",
    "Reas. Rej.",
    "Reason for Rejection",
    "Material Blk",
    "Floor limit Blk",
    "Multiple of MOQ Blk",
    "Expected Price Blk",
    "DEA Number (Customer Master)",
    "Req. Delivery Date",
    "SOM Indc.",
)

# Exact reference headers, in exact reference order, for the final
# client-facing Summary sheet, per sampo.xlsx. These are authoritative
# business headers and must NOT be auto-substituted with our internal
# preferred wording (e.g. "Avg" stays "Avg", not "Average"). Note the
# leading space in " Material Description", which matches sampo.xlsx
# exactly. The one deliberate deviation from sampo.xlsx is the comments
# column, which uses the business header "Avinash/Krishna Comments"
# rather than the sample file's person-specific "John".
#
# The three historical month columns are a POSITIONAL TEMPLATE only: the
# reference workbook always has exactly 3 month columns in this position
# (oldest -> newest completed month), but the ACTUAL header text must be
# the dynamically calculated previous-3-months labels for the current
# reporting period (e.g. "Feb"/"Mar"/"Apr" for a May run), never a fixed
# "Apr"/"May"/"Jun". See ``_summary_reference_columns`` below, which
# substitutes the real ``month_labels`` into this template position.
_SUMMARY_MONTH_SLOT_COUNT = 3


def _summary_reference_columns(month_labels: tuple[str, ...]) -> tuple[str, ...]:
    """Build the exact reference Summary header order, substituting the
    dynamically-calculated previous-3-months labels (oldest -> newest) into
    the fixed 3-column month template position. Every other header remains
    exactly as authored in the reference workbook (sampo.xlsx), except the
    comments column, which uses the business header "Avinash/Krishna
    Comments" instead of sampo.xlsx's person-specific "John"."""
    return (
        " Material Description",
        "Sold-to party Name",
        "Lookup",
        "NDC Code",
        "Max of UPS Inventory",
        "Sum of Sales Order Qty",
        "Max of Sales Qty MTD",
        "Max of Forecast Qty",
        "Avinash/Krishna Comments",
        *month_labels,
        "Avg",
        "Buying Group",
        "Award Type",
        "SC Comments",
    )




# Rename map from internal working-column names (used during aggregation)
# to the exact reference Summary headers. Note the leading space in
# " Material Description", which matches sampo.xlsx exactly.
#
# NOTE: the reference workbook (sampo.xlsx) labels the comments column
# "John", but that is a person-specific artifact of the sample file. The
# business column is "Avinash/Krishna Comments", so the client-facing POB
# Summary sheet now carries that header (no rename). The underlying values
# were always the Avinash/Krishna Comments values -- only the label changed.
SUMMARY_COLUMN_RENAMES: dict[str, str] = {
    "Average": "Avg",
    "Material Description": " Material Description",
}

# Sheets exposed in the client-facing POB.xlsx workbook. Internal
# audit/debug sheets (Sales Summary, Pivot, Audit, Exceptions) continue to
# be generated internally (see Sales_Summary.xlsx) but are not included in
# the client-facing POB.xlsx unless explicitly configured.
POB_CLIENT_FACING_SHEETS: tuple[str, ...] = ("Orderbook", "Summary")


@dataclass(frozen=True)
class Phase4Result:
    # None in production mode, where the Sales Summary is kept in memory only.
    sales_summary_path: Optional[Path]
    pob_path: Path
    row_count: int
    reporting_year: int
    reporting_month: int


def _get_first_sheet(loaded_workbooks, workbook_key: str) -> Optional[pd.DataFrame]:
    workbook_data = loaded_workbooks.get(workbook_key)
    if workbook_data is None or not workbook_data.worksheets:
        return None
    return next(iter(workbook_data.worksheets.values())).dataframe


def _build_summary_dataframe(
    aggregated_df: pd.DataFrame,
    enriched_lookup_df: pd.DataFrame,
    month_labels: tuple[str, ...],
) -> pd.DataFrame:
    """Assemble the internal Summary/Sales Summary aggregation dataframe.

    Uses internal working-column names (e.g. "Avinash/Krishna Comments",
    "Average"). This dataframe backs the internal Sales_Summary.xlsx sheets;
    the client-facing POB.xlsx Summary sheet is built separately via
    ``_to_reference_summary_dataframe`` which renames to the exact
    authoritative reference headers ("Avg") without altering this
    internal dataframe or any upstream business logic.

    SOP requirement: after "Max Forecast Qty" include Avinash/Krishna
    Comments, the previous three months, Average, then Buying Group / Award
    Type / SC Comments.
    """
    working = aggregated_df.merge(
        enriched_lookup_df,
        on="Lookup",
        how="left",
        suffixes=("", "__extra"),
    )

    internal_columns = (
        "Material Description",
        "Sold-to party Name",
        "Lookup",
        "NDC Code",
        "Max of UPS Inventory",
        "Sum of Sales Order Qty",
        "Max of Sales Qty MTD",
        "Max of Forecast Qty",
        "Avinash/Krishna Comments",
    )
    ordered_columns = list(internal_columns) + list(month_labels) + ["Average"] + ["Buying Group", "Award Type", "SC Comments"]
    for column in ordered_columns:
        if column not in working.columns:
            working[column] = pd.NA

    # Internal-only diagnostic column carried as the LAST column so it never
    # disturbs the documented SOP column order above. It is consumed by
    # report_formatter.apply_summary_action_formatting and is stripped from
    # the client-facing sheet by _to_reference_summary_dataframe.
    if SUMMARY_ACTION_FLAG_COLUMN not in working.columns:
        working[SUMMARY_ACTION_FLAG_COLUMN] = pd.NA
    ordered_columns = ordered_columns + [SUMMARY_ACTION_FLAG_COLUMN]

    return working[ordered_columns]


def _to_reference_summary_dataframe(summary_df: pd.DataFrame, month_labels: tuple[str, ...]) -> pd.DataFrame:
    """Return a copy of ``summary_df`` renamed/ordered to the exact
    authoritative reference Summary headers (client-facing only).

    This performs display-only renaming (e.g. "Average" -> "Avg"); it does
    not alter ``summary_df`` itself or any upstream calculation. The
    comments column keeps its business header ("Avinash/Krishna
    Comments") and is deliberately not renamed to sampo.xlsx's "John".
    The three historical month columns are
    selected using the actual, dynamically-calculated previous-3-months
    labels for the current reporting period (e.g. "Feb"/"Mar"/"Apr" for a
    May run) -- the reference schema's 3-column month slot is a POSITION
    only, never a fixed "Apr"/"May"/"Jun" calendar assumption. Header text
    and underlying values both come from the same ``month_labels`` columns
    already produced upstream by ``historical_sales.py``, so header and
    data always refer to the same calendar month.
    """
    working = summary_df.rename(columns=SUMMARY_COLUMN_RENAMES).copy()

    reference_columns = _summary_reference_columns(month_labels)
    for column in reference_columns:
        if column not in working.columns:
            working[column] = pd.NA

    return working[list(reference_columns)]


def _to_reference_orderbook_dataframe(enriched_df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``enriched_df`` projected/renamed/ordered to the
    exact authoritative reference Orderbook schema (client-facing only).

    Preserves order/item grain (one row per Sales Order No. + Item No.);
    performs no aggregation or row reduction. Internal processing columns
    (MOQ_Issue, Controlled_Product, Price_Issue, Price_Difference,
    Low_UPS_Inventory, SC Comments, Buying Group, Award Type, historical
    month columns, temporary/duplicate merge-artifact columns, etc.) are
    excluded because they are not part of the reference schema. This
    function does not alter ``enriched_df`` or any upstream calculation.
    """
    working = enriched_df.rename(columns=ORDERBOOK_COLUMN_RENAMES).copy()

    # The rename above can produce a duplicate "Pack Size (MOQ)" column: the
    # raw orderbook's own "PackSize(MOQ)" column is renamed to match the
    # reference header, but a second "Pack Size (MOQ)" column already exists
    # on enriched_df from the MOQ Master join. Both represent the same
    # business concept (pack size / MOQ); this coalesces them into a single
    # reference column (preferring the MOQ Master-enriched value, falling
    # back to the original orderbook value when the MOQ Master join did not
    # find a match) without altering enriched_df or any upstream merge
    # logic -- this is a display-only projection step.
    duplicate_columns = [index for index, column in enumerate(working.columns) if column == "Pack Size (MOQ)"]
    if len(duplicate_columns) > 1:
        pack_size_frame = working.iloc[:, duplicate_columns]
        # Prefer the MOQ Master-enriched value (rightmost duplicate, added
        # later during the Phase 3 merge) and fall back to the original
        # orderbook value (leftmost duplicate) when the MOQ Master join did
        # not find a match for that row.
        coalesced = pack_size_frame.iloc[:, ::-1].bfill(axis=1).iloc[:, 0]
        working = working.loc[:, [column != "Pack Size (MOQ)" for column in working.columns]]
        working["Pack Size (MOQ)"] = coalesced

    for column in ORDERBOOK_REFERENCE_COLUMNS:
        if column not in working.columns:
            working[column] = pd.NA

    return working[list(ORDERBOOK_REFERENCE_COLUMNS)]


def _validate_orderbook_grain(master_df: pd.DataFrame, orderbook_df: pd.DataFrame, logger) -> None:
    """Validate that the final Orderbook sheet preserves all Business Master
    order/item records at the same grain (one row per Sales Order No. +
    Item No.), raising no exception but logging/collecting any dropped keys
    so they can be surfaced via the Exceptions sheet.
    """
    key_columns = ("Sales Order No.", "Item No.")
    if not all(column in master_df.columns for column in key_columns) or not all(
        column in orderbook_df.columns for column in key_columns
    ):
        logger.warning("Cannot validate Orderbook grain: Sales Order No./Item No. missing from master or Orderbook dataframe")
        return

    master_keys = set(zip(master_df["Sales Order No."], master_df["Item No."]))
    orderbook_keys = set(zip(orderbook_df["Sales Order No."], orderbook_df["Item No."]))
    dropped_keys = master_keys - orderbook_keys

    if len(master_df) != len(orderbook_df):
        logger.warning(
            "Orderbook row count (%s) does not match Business Master row count (%s)",
            len(orderbook_df),
            len(master_df),
        )
    if dropped_keys:
        logger.warning("Dropped Sales Order No./Item No. records from final Orderbook: %s", dropped_keys)
    else:
        logger.info(
            "Orderbook grain validation passed | master_rows=%s | orderbook_rows=%s | dropped_records=0",
            len(master_df),
            len(orderbook_df),
        )


def run_phase4(
    loaded_workbooks,
    master_df: pd.DataFrame,
    ups_inventory_df: Optional[pd.DataFrame],
    moq_validation_df: Optional[pd.DataFrame],
    config,
    logger,
) -> Phase4Result:
    """Run Phase 4: Sales Summary, business rules, final aggregation, and POB.xlsx.

    Reuses Phase 1 loaded workbooks, Phase 2 derived results
    (``ups_inventory_df``/``moq_validation_df``, passed in directly from the
    already-computed Phase 2 result -- never recalculated here), and the
    Phase 3 Business Master dataframe. Does not reload or recompute any
    Phase 1-3 calculation.
    """
    strend_df = _get_first_sheet(loaded_workbooks, "sales_trend")
    cip_df = _get_first_sheet(loaded_workbooks, "critical_inventory_tracker")

    if strend_df is None:
        raise ValueError("Phase 4 requires the Sales Trend (Strend) source, which was not loaded")

    # Step: determine reporting period dynamically from PO date in the
    # Business Master (no hardcoded months).
    reporting_year, reporting_month = determine_reporting_period(master_df, "PO date", logger)

    working_df = master_df.copy()

    # Ensure a Lookup column exists (Phase 3 already builds this when
    # possible; recomputed only as a last resort using the same rule).
    if "Lookup" not in working_df.columns:
        if "NDC Code" in working_df.columns and "Sold-to party Name" in working_df.columns:
            working_df["Lookup"] = (
                working_df["NDC Code"].apply(normalize_ndc_key).fillna("")
                + working_df["Sold-to party Name"].apply(normalize_text_key).fillna("")
            )
            working_df["Lookup"] = working_df["Lookup"].replace("", pd.NA)
        else:
            raise ValueError("Cannot proceed without a Lookup key; NDC Code and Sold-to party Name are both unavailable")

    historical_result = build_historical_sales(
        strend_df,
        working_df["Lookup"],
        reporting_year,
        reporting_month,
        logger,
    )

    enrichment_result = enrich_master_with_phase2_and_cip(
        working_df,
        ups_inventory_df=ups_inventory_df,
        moq_validation_df=moq_validation_df,
        cip_df=cip_df,
        logger=logger,
    )
    enriched_df = enrichment_result.dataframe

    enriched_df, rule_stats = apply_business_rules(
        enriched_df,
        material_description_column="Material Description",
        unit_price_column="Unit Price",
        wac_bg_price_column="WAC/BG price in EDI",
        ups_inventory_column="UPS Inventory",
        moq_issue_column="MOQ_Issue",
        logger=logger,
    )

    enriched_df = merge_historical_sales(
        enriched_df,
        historical_result.dataframe,
        historical_result.previous_month_labels,
        "Lookup",
        logger,
    )

    aggregation_result = build_sales_summary_aggregation(enriched_df, logger)
    aggregated_df = aggregation_result.dataframe

    # Per-Lookup enrichment fields to attach onto the aggregated rows
    # (aggregation collapses to one row per Material/Customer/Lookup/NDC,
    # so enrichment fields are taken from the first matching detail row).
    enrichment_columns = [
        "Lookup",
        "Avinash/Krishna Comments",
        "Buying Group",
        "Award Type",
        "SC Comments",
    ] + list(historical_result.previous_month_labels) + ["Average"]
    enrichment_columns = [column for column in enrichment_columns if column in enriched_df.columns or column == "Lookup"]
    enriched_lookup_df = enriched_df[enrichment_columns].drop_duplicates(subset="Lookup", keep="first")

    summary_df = _build_summary_dataframe(aggregated_df, enriched_lookup_df, historical_result.previous_month_labels)

    # ---------------- Sales_Summary.xlsx (DEBUG-ONLY ARTIFACT) ----------------
    # ``summary_df`` is already in memory and is what backs the client-facing
    # POB "Summary" sheet below, so skipping this workbook cannot change any
    # business value. In production only POB.xlsx is written.
    debug_mode = bool(getattr(config, "debug_mode", False))
    sales_summary_path: Optional[Path] = None

    if debug_mode:
        sales_summary_workbook = Workbook()
        sales_summary_ws = write_dataframe_sheet(sales_summary_workbook, "Sales Summary", summary_df)
        # BUSINESS RULE: the low UPS Inventory yellow highlight lives on the
        # aggregated "Max of UPS Inventory" column, and NOT on the
        # client-facing POB.xlsx "Orderbook" sheet's "UPS Inventory" column.
        low_inventory_highlight_count = apply_low_ups_inventory_formatting(sales_summary_ws)
        logger.info(
            "Sales Summary low UPS Inventory highlight | highlighted_cells=%s",
            low_inventory_highlight_count,
        )
        sales_summary_cancel_rows, sales_summary_hold_rows = apply_summary_action_formatting(
            sales_summary_ws, summary_df
        )
        logger.info(
            "Sales Summary Action row colouring | cancel_rows=%s | hold_rows=%s",
            sales_summary_cancel_rows,
            sales_summary_hold_rows,
        )

        audit_df = pd.DataFrame(
            [
                {
                    "Total Master Rows": int(len(master_df)),
                    "Aggregated Rows": int(len(aggregated_df)),
                    "Unique Lookup Values": aggregation_result.unique_lookup_count,
                    "Duplicate Lookup Values": aggregation_result.duplicate_lookup_count,
                    "Reporting Year": reporting_year,
                    "Reporting Month": reporting_month,
                    "Historical Matches": historical_result.matched_lookup_count,
                    "Historical Misses": historical_result.missing_lookup_count,
                    "Duplicate Historical Keys": historical_result.duplicate_lookup_keys,
                }
            ]
        )
        write_dataframe_sheet(sales_summary_workbook, "Audit", audit_df)

        # Diagnostics for the dedicated SC Comments lookup. This is an internal
        # audit sheet on Sales_Summary.xlsx only; the client-facing POB.xlsx
        # sheet set (POB_CLIENT_FACING_SHEETS) is unchanged.
        if enrichment_result.sc_comments_exceptions_df is not None and not enrichment_result.sc_comments_exceptions_df.empty:
            write_dataframe_sheet(
                sales_summary_workbook,
                "SC_Comments_Exceptions",
                enrichment_result.sc_comments_exceptions_df,
            )

        exceptions_rows = []
        if historical_result.missing_lookup_count > 0:
            exceptions_rows.append({"Type": "MISSING_HISTORICAL_SALES", "Count": historical_result.missing_lookup_count})
        if historical_result.duplicate_lookup_keys > 0:
            exceptions_rows.append({"Type": "DUPLICATE_HISTORICAL_KEY", "Count": historical_result.duplicate_lookup_keys})
        exceptions_df = pd.DataFrame(exceptions_rows) if exceptions_rows else pd.DataFrame(columns=["Type", "Count"])
        write_dataframe_sheet(sales_summary_workbook, "Exceptions", exceptions_df)

        sales_summary_path = config.output_dir / "Sales_Summary.xlsx"
        save_workbook(sales_summary_workbook, sales_summary_path)
        logger.info("[DEBUG] Wrote Sales Summary workbook to %s", sales_summary_path)
    else:
        logger.info("Sales Summary kept in memory (production mode; no intermediate workbook written)")

    # ---------------- POB.xlsx (client-facing) ----------------
    # Validate that the final Orderbook preserves the Business Master
    # order/item grain before writing (no aggregation, no row reduction).
    _validate_orderbook_grain(master_df, enriched_df, logger)

    pob_workbook = Workbook()

    reference_orderbook_df = _to_reference_orderbook_dataframe(enriched_df)
    orderbook_ws = write_dataframe_sheet(pob_workbook, "Orderbook", reference_orderbook_df)
    apply_business_rule_formatting(orderbook_ws, enriched_df)

    reference_summary_df = _to_reference_summary_dataframe(summary_df, historical_result.previous_month_labels)
    summary_ws = write_dataframe_sheet(pob_workbook, "Summary", reference_summary_df)
    # BUSINESS RULE: the same low UPS Inventory yellow highlight applied to
    # Sales_Summary.xlsx also applies to the client-facing POB.xlsx Summary
    # sheet, which carries the identical "Max of UPS Inventory" header. Only
    # that cell is filled; the POB "Orderbook" sheet's "UPS Inventory"
    # column is deliberately NOT highlighted.
    pob_summary_highlight_count = apply_low_ups_inventory_formatting(summary_ws)
    logger.info(
        "POB Summary low UPS Inventory highlight | highlighted_cells=%s",
        pob_summary_highlight_count,
    )

    # BUSINESS RULE: the Orderbook sheet's Cancel = red / Hold = blue row
    # colouring is mirrored onto the aggregated Summary sheet, using the
    # rollup flag computed during aggregation (any Cancel -> Cancel, else
    # any Hold -> Hold). Applied AFTER the yellow highlight above so a
    # Cancel/Hold row takes full precedence, exactly as on the Orderbook
    # sheet.
    summary_cancel_rows, summary_hold_rows = apply_summary_action_formatting(summary_ws, summary_df)
    logger.info(
        "POB Summary Action row colouring | cancel_rows=%s | hold_rows=%s",
        summary_cancel_rows,
        summary_hold_rows,
    )

    # Internal audit/debug sheets (Sales Summary, Pivot, Audit, Exceptions)
    # are generated internally in Sales_Summary.xlsx above. They are
    # intentionally NOT included in the client-facing POB.xlsx per the
    # authoritative reference workbook, which contains only Orderbook and
    # Summary. To keep them available for internal debugging, they are
    # still added to the same workbook object below, but only when
    # explicitly enabled via config; by default POB.xlsx contains exactly
    # the two client-facing sheets.
    include_internal_sheets = bool(getattr(config, "pob_include_internal_sheets", False))
    if include_internal_sheets:
        internal_summary_ws = write_dataframe_sheet(pob_workbook, "Sales Summary", summary_df)
        apply_low_ups_inventory_formatting(internal_summary_ws)
        apply_summary_action_formatting(internal_summary_ws, summary_df)
        write_dataframe_sheet(pob_workbook, "Pivot", aggregated_df)

        pob_audit_rows = {
            "Total Master Rows": int(len(master_df)),
            "Unique NDCs": int(enriched_df["NDC Code"].nunique(dropna=True)) if "NDC Code" in enriched_df.columns else 0,
            "Unique Lookup Values": int(enriched_df["Lookup"].nunique(dropna=True)) if "Lookup" in enriched_df.columns else 0,
            "Controlled Products": rule_stats.controlled_product_count,
            "Price Issues": rule_stats.price_issue_count,
            "MOQ Issues": rule_stats.moq_issue_count,
            "Low UPS Inventory Rows": rule_stats.low_ups_inventory_count,
            "Historical Sales Matches": historical_result.matched_lookup_count,
            "Historical Sales Misses": historical_result.missing_lookup_count,
            "Missing SC Comments": enrichment_result.sc_comments_missing,
            "Missing Buying Groups": enrichment_result.buying_group_missing,
            "Missing Awards": enrichment_result.award_missing,
        }
        write_dataframe_sheet(pob_workbook, "Audit", pd.DataFrame([pob_audit_rows]))

        pob_exceptions_rows = []
        if historical_result.missing_lookup_count > 0:
            pob_exceptions_rows.append({"Type": "MISSING_HISTORICAL_SALES", "Count": historical_result.missing_lookup_count})
        if historical_result.duplicate_lookup_keys > 0:
            pob_exceptions_rows.append({"Type": "DUPLICATE_HISTORICAL_KEY", "Count": historical_result.duplicate_lookup_keys})
        if enrichment_result.sc_comments_missing > 0:
            pob_exceptions_rows.append({"Type": "MISSING_SC_COMMENTS", "Count": enrichment_result.sc_comments_missing})
        if enrichment_result.buying_group_missing > 0:
            pob_exceptions_rows.append({"Type": "MISSING_BUYING_GROUP", "Count": enrichment_result.buying_group_missing})
        if enrichment_result.award_missing > 0:
            pob_exceptions_rows.append({"Type": "MISSING_AWARD", "Count": enrichment_result.award_missing})
        if rule_stats.price_issue_count > 0:
            pob_exceptions_rows.append({"Type": "PRICE_ISSUE", "Count": rule_stats.price_issue_count})
        if rule_stats.moq_issue_count > 0:
            pob_exceptions_rows.append({"Type": "MOQ_ISSUE", "Count": rule_stats.moq_issue_count})
        if rule_stats.low_ups_inventory_count > 0:
            pob_exceptions_rows.append({"Type": "LOW_UPS_INVENTORY", "Count": rule_stats.low_ups_inventory_count})

        pob_exceptions_df = pd.DataFrame(pob_exceptions_rows) if pob_exceptions_rows else pd.DataFrame(columns=["Type", "Count"])
        write_dataframe_sheet(pob_workbook, "Exceptions", pob_exceptions_df)

    pob_path = config.output_dir / "POB.xlsx"
    save_workbook(pob_workbook, pob_path)
    logger.info("Wrote final POB workbook to %s", pob_path)

    return Phase4Result(
        sales_summary_path=sales_summary_path,
        pob_path=pob_path,
        row_count=len(enriched_df),
        reporting_year=reporting_year,
        reporting_month=reporting_month,
    )
