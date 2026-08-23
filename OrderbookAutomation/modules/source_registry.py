from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class SourceDefinition:
    """Describes a logical input source in a filename-independent way.

    Instead of pointing at a specific file on disk, a source is identified by
    the *shape* of its data: the exact business headers it must contain, plus
    an optional list of preferred worksheet names to try first. This allows
    the underlying Excel file to be renamed, re-saved, or re-dated (e.g. a
    daily inventory export) without breaking discovery.

    Attributes:
        logical_name: Stable internal key used throughout the pipeline
            (matches the historical ``workbook_specs`` keys so downstream
            code such as Phase 2/Phase 3 does not need to change).
        display_name: Human/business-friendly name used in error messages
            and logs (e.g. "Daily Inventory").
        required_headers: Exact business column names that MUST be present
            (case-sensitive, unmodified) for a worksheet to be considered a
            match for this source. Never renamed/normalized.
        optional_headers: Exact business column names that are nice-to-have.
            Missing optional headers never fail validation.
        preferred_sheet_names: Worksheet names to prefer when a workbook
            contains multiple worksheets that could match (tried in order).
        filename_hint: Optional, soft, human-readable hint describing what
            kind of filename to expect. This is NEVER used as a matching
            rule by itself -- it exists purely for error messages so a
            business user knows what to look for.
        filename_keywords: Optional, soft, case-insensitive filename
            substrings used ONLY as a tiebreaker when two or more files have
            byte-for-byte identical header rows (e.g. a real data file and a
            header-only template/reference copy). Never used as the primary
            matching rule -- header content is always checked first.
        mandatory: When True (default), discovery/validation fail the
            pipeline if this source cannot be found in the input folder.
            When False, the source is treated as optional: discovery simply
            omits it from the resolved set (no error raised), and downstream
            phases that depend on it must handle its absence gracefully.
    """

    logical_name: str
    display_name: str
    required_headers: Sequence[str]
    optional_headers: Sequence[str] = field(default_factory=tuple)
    preferred_sheet_names: Sequence[str] = field(default_factory=tuple)
    filename_hint: str = ""
    filename_keywords: Sequence[str] = field(default_factory=tuple)
    mandatory: bool = True


# Logical source registry. Keys match the historical `workbook_specs` keys
# used across Phase 1/2/3 so no downstream code needed to change its lookup
# keys. Only *how* a source is located changed (header-based discovery
# instead of a fixed filename).
SOURCE_DEFINITIONS: dict[str, SourceDefinition] = {
    "orderbook": SourceDefinition(
        logical_name="orderbook",
        display_name="Orderbook",
        required_headers=(
            "Sales Order No.",
            "NDC Code",
            "Sold-to party Name",
            "PackSize(MOQ)",
        ),
        optional_headers=(
            "Item No.",
            "Matl.Code",
            "Material Description",
            "Total Stock In-hand",
            "Sales Order Qty",
            "Sales Qty MTD",
            "Forecast Qty",
            "Sold-to party",
            "S.O. Type",
            "Unit Price",
            "WAC/BG price in EDI",
            "PO number",
            "PO date",
            "Ship-to party",
            "Ship-to party Name",
            "Req. Delivery Date",
            "SOM Indc.",
        ),
        preferred_sheet_names=("UOB", "Sheet1"),
        filename_hint="Orderbook export (e.g. raw_OB.xlsx)",
    ),
    "moq": SourceDefinition(
        logical_name="moq",
        display_name="Material Description / MOQ Master",
        required_headers=("HANA Material", "NDC code", "Material Description"),
        optional_headers=("MOQ ",),
        preferred_sheet_names=("Sheet1",),
        filename_hint="Material Description / MOQ / Material Number export",
    ),
    "inventory": SourceDefinition(
        logical_name="inventory",
        display_name="Daily Inventory",
        required_headers=("NDC", "Actual Quantity", "Inventory"),
        optional_headers=("SKU", "Description", "Allocated Quantity"),
        preferred_sheet_names=("Sheet1",),
        filename_hint="Daily inventory export (date-stamped filename, e.g. 07-30_inv.xlsx)",
    ),
    "open_order_summary": SourceDefinition(
        logical_name="open_order_summary",
        display_name="Open Order Summary",
        required_headers=("SKU", " Total ", "Pickticket Status"),
        # "Customer Group" is a fallback (priority 3) Buying Group mapping
        # column consumed by modules/buying_group_lookup.py. It is optional
        # so its absence never fails discovery for this source.
        optional_headers=("IM_SKU_DESC", "PH_SOLDTO_NAME", "SO#", "Customer Group"),
        preferred_sheet_names=("Sheet1",),
        filename_hint="Open Order Summary export",
    ),
    "buying_groups": SourceDefinition(
        logical_name="buying_groups",
        display_name="Buying Groups",
        required_headers=("Customer", "Customer buying group"),
        preferred_sheet_names=("Sheet1",),
        filename_hint="Buying Groups mapping file",
    ),
    "awards": SourceDefinition(
        logical_name="awards",
        display_name="Awards",
        required_headers=("NDC", "Customer"),
        optional_headers=("Award Type", "Description", "Sold to party", "Lookup"),
        preferred_sheet_names=("Sheet1",),
        filename_hint="Awards export",
    ),
    "critical_inventory_tracker": SourceDefinition(
        logical_name="critical_inventory_tracker",
        display_name="Critical Inventory Tracker (CIP)",
        required_headers=("NDC", "Comments"),
        optional_headers=("Customer ETA", "Description"),
        preferred_sheet_names=("Sheet1",),
        filename_hint="Critical Inventory / CIP tracker export",
    ),
    "morning_completed_orderbook": SourceDefinition(
        logical_name="morning_completed_orderbook",
        display_name="Morning Completed Order Book",
        # Pre-processed/completed orderbook produced by the morning run.
        #
        # ONLY "Sales Order Qty" is consumed from this file -- every other
        # column (INCLUDING its own "UPS Inventory") is deliberately ignored.
        # UPS Inventory is always recomputed as
        # MAX(0, Inventory - Total - Sales Order Qty) so this file can never
        # double-count.
        #
        # Because the data is already processed, NO row filtering is applied
        # (unlike upload_sheet, which filters on Reason Code / Action).
        #
        # DISCRIMINATORS: "UPS Inventory" and "Sales Value (FC)" appear in no
        # other registered source. Both are kept required so a single upstream
        # column change cannot cause a mis-match. Note this file also carries
        # "Pack Size (MOQ)" (spaced), which is distinct from the Orderbook's
        # "PackSize(MOQ)" (unspaced), so it can never match 'orderbook'.
        required_headers=(
            "Sales Order No.",
            "NDC Code",
            "Sales Order Qty",
            "UPS Inventory",
            "Sales Value (FC)",
        ),
        optional_headers=(
            "Item No.",
            "Lookup",
            "Material Description",
            "Pack Size (MOQ)",
            "Sold-to party Name",
            "Action",
            "Reason for Rejection",
            "DEA Number (Customer Master)",
        ),
        preferred_sheet_names=("Sheet1",),
        filename_hint="Morning completed/processed order book",
        filename_keywords=("morning", "completed"),
        # Not individually mandatory -- the PAIR (this OR upload_sheet) is
        # enforced in derived_dataset_manager.run_phase2().
        mandatory=False,
    ),
    "sales_trend": SourceDefinition(
        logical_name="sales_trend",
        display_name="Sales Trend (Strend)",
        required_headers=("Material Description", "Cust Group"),
        optional_headers=("NDC Code", "Sold-to party Name"),
        preferred_sheet_names=("Sheet1",),
        filename_hint="Sales trend export (Strend)",
    ),
    "upload_sheet": SourceDefinition(
        logical_name="upload_sheet",
        display_name="Upload Sheet",
        # Discovered ONLY by header signature -- the client may name this file
        # anything (e.g. "upload sheet.xlsx", "Upload_2026-08-21.xlsx").
        #
        # COLLISION NOTE: "NDC Code", "Sales Order Qty" and "Action" all also
        # appear in the Orderbook source. "Reason Code" is therefore the SOLE
        # discriminating header between this source and "orderbook". All four
        # headers are kept required (rather than a narrower signature) so the
        # combined signature stays specific enough to avoid a false match.
        # If the Orderbook export ever gains a "Reason Code" column, this
        # source MUST be given an additional discriminating required header.
        required_headers=(
            "NDC Code",
            "Reason Code",
            "Action",
            "Sales Order Qty",
        ),
        optional_headers=(
            "Sales Order No.",
            "Material Description",
            "Sold-to party Name",
        ),
        preferred_sheet_names=("Sheet1",),
        filename_hint="Upload / order-adjustment sheet (optional; e.g. upload sheet.xlsx)",
        # Soft tiebreaker only -- never a primary matching rule.
        filename_keywords=("upload",),
        # Pipeline must still run when this file is absent (UPS falls back to
        # Upload_Qty = 0).
        mandatory=False,
    ),
}
