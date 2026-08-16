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
    """

    logical_name: str
    display_name: str
    required_headers: Sequence[str]
    optional_headers: Sequence[str] = field(default_factory=tuple)
    preferred_sheet_names: Sequence[str] = field(default_factory=tuple)
    filename_hint: str = ""
    filename_keywords: Sequence[str] = field(default_factory=tuple)


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
        optional_headers=("IM_SKU_DESC", "PH_SOLDTO_NAME", "SO#"),
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
    "sales_summary": SourceDefinition(
        logical_name="sales_summary",
        display_name="Sales Summary",
        required_headers=("Sales Order No.", "NDC Code", "Lookup"),
        optional_headers=("Pack Size (MOQ)", "Sales Order Qty", "Sales Qty MTD", "Forecast Qty"),
        preferred_sheet_names=("Sheet1",),
        filename_hint="Sales summary export",
        # "Headers.xlsx" is a header-template reference copy that shares an
        # identical header row with the real sales summary export. Filename
        # keywords are used only to break that specific tie, never as the
        # primary discovery rule.
        filename_keywords=("sales_summ", "sales summary"),
    ),
    "sales_trend": SourceDefinition(
        logical_name="sales_trend",
        display_name="Sales Trend (Strend)",
        required_headers=("Material Description", "Cust Group"),
        optional_headers=("NDC Code", "Sold-to party Name"),
        preferred_sheet_names=("Sheet1",),
        filename_hint="Sales trend export (Strend)",
    ),
}
