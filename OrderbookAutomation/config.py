from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Sequence

from modules.source_registry import SOURCE_DEFINITIONS, SourceDefinition
from modules.utils import get_application_base_dir


# ---------------------------------------------------------------------------
# DEBUG MODE (OUTPUT-ONLY SWITCH)
# ---------------------------------------------------------------------------
# PRODUCTION DEFAULT: False.
#
# This flag controls OUTPUT ARTIFACTS ONLY. It NEVER changes any business
# calculation, merge rule, filter, threshold or formatting rule. Every phase
# performs exactly the same computation in both modes; the only difference is
# whether the intermediate/diagnostic workbooks and markdown documents are
# additionally serialized to disk.
#
#   DEBUG_MODE = False (production / client EXE)
#       output/  ->  POB.xlsx ONLY
#
#   DEBUG_MODE = True (developer)
#       output/  ->  POB.xlsx plus Workbook_Profile.xlsx, Derived_Data.xlsx,
#                    Business_Master_Data.xlsx, Sales_Summary.xlsx
#       docs/    ->  DATA_DICTIONARY.md, JOIN_KEY_ANALYSIS.md
#
# Developers can enable diagnostics WITHOUT editing this file by setting the
# environment variable ORDERBOOK_DEBUG=1 (also accepts "true"/"yes"/"on").
DEBUG_MODE: bool = False

_DEBUG_ENV_VAR = "ORDERBOOK_DEBUG"
_TRUTHY_VALUES = {"1", "true", "yes", "on"}


def is_debug_mode() -> bool:
    """Return True when diagnostic/intermediate outputs should be written.

    Resolution order:
      1. ``ORDERBOOK_DEBUG`` environment variable, when set (developer
         override that requires no code edit and no rebuild).
      2. The ``DEBUG_MODE`` constant above (production default: False).

    OUTPUT-ONLY: callers must use this exclusively to decide whether to
    SERIALIZE a diagnostic artifact. It must never gate a calculation.
    """
    raw_value = os.environ.get(_DEBUG_ENV_VAR)
    if raw_value is not None and raw_value.strip():
        return raw_value.strip().lower() in _TRUTHY_VALUES
    return DEBUG_MODE


# The single client-facing business output produced by a production run.
# Allow-list of files this application is known to generate inside output/.
# ONLY these exact filenames may be removed during pre-run cleanup, so any
# unrelated file a user has placed in output/ is always left untouched.
APPLICATION_GENERATED_OUTPUT_FILES: tuple[str, ...] = (
    "Workbook_Profile.xlsx",
    "Derived_Data.xlsx",
    "Business_Master_Data.xlsx",
    "Sales_Summary.xlsx",
)

# Diagnostic markdown documents written under docs/ in DEBUG mode only.
APPLICATION_GENERATED_DOC_FILES: tuple[str, ...] = (
    "DATA_DICTIONARY.md",
    "JOIN_KEY_ANALYSIS.md",
)


# Backward-compatible business column mappings used by legacy lookup/merge modules.
ORDERBOOK_COLUMNS = {
    "sales_order_number": "Sales Order No.",
    "item_number": "Item No.",
    "material_code": "Matl.Code",
    "ndc_code": "NDC Code",
    "material_description": "Material Description",
    "sales_order_qty": "Sales Order Qty",
    "sales_qty_mtd": "Sales Qty MTD",
    "forecast_qty": "Forecast Qty",
    "sold_to_party": "Sold-to party",
    "sold_to_party_name": "Sold-to party Name",
    "ship_to_party": "Ship-to party",
    "unit_price": "Unit Price",
    "sales_value_fc": "Sales Value FC",
    "wac_bg_price_in_edi": "WAC/BG Price in EDI",
    "po_number": "PO Number",
    "postal_code": "Postal Code",
}

LOOKUP_COLUMNS = {
    "material_code": "HANA Material",
    "ndc_code": "NDC Code",
    "material_description": "Material Description",
    "pack_size_moq": "MOQ ",
}

INVENTORY_COLUMNS = {
    "ndc": "NDC",
    "sku": "SKU",
    "description": "Description",
    "actual_quantity": "Actual Quantity",
    "allocated_quantity": "Allocated Quantity",
    "inventory": "Inventory",
    "hold_codes": "Hold Codes",
}

OPEN_ORDER_COLUMNS = {
    "sku": "SKU",
    "total": " Total ",
    "im_sku_desc": "IM_SKU_DESC",
    "ph_soldto_name": "PH_SOLDTO_NAME",
    "customer_group": "Customer Group",
    "pickticket_status": "Pickticket Status",
    "lookup": "x",
    "no_of_days": "No of days",
    "so_number": "SO#",
}

BUYING_GROUP_COLUMNS = {
    "buying_group": "Customer buying group",
    "customer": "Customer",
}

AWARDS_COLUMNS = {
    "award_type": "Award Type",
    "description": "Description",
    "customer": "Customer",
    "sold_to_party": "Sold to party",
    "lookup": "Lookup",
    "ndc": "NDC",
}

CIP_COLUMNS = {
    "comments": "Comments",
    "customer_eta": "Customer ETA",
    "description": "Description",
    "ndc": "NDC",
}

SALES_SUMMARY_COLUMNS = {
    "sales_order_number": "Sales Order No.",
    "item_number": "Item No.",
    "material_code": "Matl._x000d_\nCode",
    "sales_order_qty": "Sales Order Qty",
    "sales_qty_mtd": "Sales Qty MTD",
    "forecast_qty": "Forecast Qty",
    "material_description": "Material Description",
    "pack_size": "Pack Size (MOQ)",
    "lookup": "Lookup",
    "ndc_code": "NDC Code",
    "sold_to_party": "Sold-to party",
    "sold_to_party_name": "Sold-to party Name",
}

SALES_TREND_COLUMNS = {
    "material_description": "Material Description",
    "customer_group": "Cust Group",
    "contract_id": " Cont ID ",
    "lookup": "x",
    "ndc_code": "NDC Code",
    "sold_to_party_name": "Sold-to party Name",
}


@dataclass(frozen=True)
class BuyingGroupSource:
    """One authoritative Customer -> Buying Group mapping source.

    ``Buying_groups.xlsx`` is only ONE of several workbooks supplied to the
    application that carry a customer-to-group mapping, and it is known to
    be incomplete. Each entry below declares, for a single logical source:

    - ``dataframe_key``: the key under which Phase 3 passes this source's
      dataframe into ``build_master_workbook(source_frames=...)``.
    - ``display_name``: the business-facing source filename recorded in the
      "Buying Group Source" lineage column and audit sheet.
    - ``customer_column`` / ``buying_group_column``: the EXACT business
      header names in that source. These are never renamed or normalized on
      disk; only temporary normalized match keys are derived from them.
    - ``priority``: 1 = highest. Lower-priority sources are consulted ONLY
      as a fallback, and a higher-priority value always wins a cross-source
      disagreement (this is a deterministic resolution, NOT a conflict).

    A DUPLICATE_CONFLICT is raised only when a single priority tier maps one
    normalized customer to two or more distinct Buying Group values, because
    only then is there no deterministic rule available to choose between them.
    """

    dataframe_key: str
    display_name: str
    customer_column: str
    buying_group_column: str
    priority: int


# Authoritative Buying Group sources, in resolution priority order.
# Priority 1 is the dedicated, business-maintained Buying Group master.
# Priorities 2/3 are broader-coverage operational exports consulted only
# when a customer is absent from every higher-priority source.
BUYING_GROUP_SOURCES: Sequence[BuyingGroupSource] = (
    BuyingGroupSource(
        dataframe_key="buying_groups",
        display_name="Buying_groups.xlsx",
        customer_column=BUYING_GROUP_COLUMNS["customer"],
        buying_group_column=BUYING_GROUP_COLUMNS["buying_group"],
        priority=1,
    ),
    BuyingGroupSource(
        dataframe_key="sales_trend",
        display_name="Strend.xlsx",
        customer_column=SALES_TREND_COLUMNS["sold_to_party_name"],
        buying_group_column=SALES_TREND_COLUMNS["customer_group"],
        priority=2,
    ),
    BuyingGroupSource(
        dataframe_key="open_orders",
        display_name="Open_Order_Summary.xlsx",
        customer_column=OPEN_ORDER_COLUMNS["ph_soldto_name"],
        buying_group_column=OPEN_ORDER_COLUMNS["customer_group"],
        priority=3,
    ),
)


@dataclass(frozen=True)
class Phase2Config:
    """Configuration for Phase 2 derived dataset generation."""

    derived_workbook_name: str
    open_order_excluded_statuses: Sequence[str]
    sku_delimiter: str
    sku_segment_widths: Sequence[int]
    # Target widths of each NDC segment produced from a SKU. A warehouse SKU
    # such as "64380-161-01" carries a 3-digit product segment, while the
    # business NDC key is the 11-digit 5-4-2 form ("64380016101"). Each SKU
    # segment is therefore left zero-padded to the width below before the
    # segments are concatenated into the NDC join key. Widths must be >= the
    # corresponding ``sku_segment_widths`` entry.
    ndc_segment_widths: Sequence[int] = (5, 4, 2)


@dataclass(frozen=True)
class AppConfig:
    """Application configuration.

    Note: input workbooks are no longer identified by fixed filenames. See
    ``modules/source_registry.py`` for the header/worksheet-based source
    definitions and ``modules/source_discovery.py`` for how they are
    resolved to actual files at runtime.
    """

    project_root: Path
    input_dir: Path
    output_dir: Path
    logs_dir: Path
    docs_dir: Path
    source_definitions: Dict[str, SourceDefinition]
    join_key_hints: Dict[str, Sequence[str]]
    phase2: Phase2Config
    # OUTPUT-ONLY switch (see is_debug_mode above). Never gates a calculation.
    debug_mode: bool = False


def get_default_config() -> AppConfig:
    # Resolve the application's home directory dynamically. When bundled into
    # a standalone .exe (e.g. via PyInstaller), this resolves to the folder
    # containing the .exe. When run as a normal Python script, it resolves to
    # the project folder. Either way, business users can simply drop their
    # input Excel files next to the executable/project and re-run it, without
    # ever editing paths in code.
    project_root = get_application_base_dir()
    input_dir = project_root / "input"
    # Fall back to the project root itself if a dedicated "input" folder was
    # not created, so the app also works if files are dropped directly
    # alongside the executable.
    if not input_dir.exists() or not any(input_dir.glob("*.xlsx")):
        if any(project_root.glob("*.xlsx")):
            input_dir = project_root
        elif not getattr(sys, "frozen", False) and any(project_root.parent.glob("*.xlsx")):
            # Development convenience only: supports the current workspace
            # layout where sample workbooks live one folder above the
            # application folder. This fallback is explicitly disabled when
            # running as a packaged/frozen EXE (see the `sys.frozen` guard
            # above) so a client machine can never silently discover
            # unrelated Excel files one level above the install folder.
            # Packaged/production layouts are expected to use
            # <APPLICATION_ROOT>/input/ or place files directly alongside
            # the executable, both of which are already handled above.
            input_dir = project_root.parent

    # Hints only, not hardcoded join behavior.
    join_key_hints = {
        "NDC": ("NDC", "NDC code", "NDC Code"),
        "Material Number": ("HANA Material", "Matl._x000d_\nCode", "Material Number"),
        "Customer": ("Customer", "Sold-to party Name", "PH_SOLDTO_NAME"),
        "Sold-to Party": ("Sold-to party", "Sold to party", "PH_SOLDTO_NAME"),
        "Lookup": ("Lookup", "x"),
        "SKU": ("SKU",),
        "Sales Order": ("Sales Order No.", "SO#", "Sales Order Qty"),
    }

    return AppConfig(
        project_root=project_root,
        input_dir=input_dir,
        output_dir=project_root / "output",
        logs_dir=project_root / "logs",
        docs_dir=project_root / "docs",
        source_definitions=SOURCE_DEFINITIONS,
        join_key_hints=join_key_hints,
        debug_mode=is_debug_mode(),
        phase2=Phase2Config(
            derived_workbook_name="Derived_Data.xlsx",
            open_order_excluded_statuses=("Pick Completed", "Loaded"),
            sku_delimiter="-",
            sku_segment_widths=(5, 3, 2),
            ndc_segment_widths=(5, 4, 2),
        ),
    )
