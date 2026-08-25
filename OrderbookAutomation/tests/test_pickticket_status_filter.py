"""Tests for the Open Order Summary Pickticket Status allow-list.

BUSINESS RULE: only rows whose Pickticket Status is one of

    In Distribution
    In Picking
    Ready for Pickroot Creation
    Ready for Wave Creation

consume inventory when UPS Inventory is derived. Every other status
(Pick Completed, Loaded, or any unknown/future value) is ignored.
"""

from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import INVENTORY_COLUMNS, OPEN_ORDER_COLUMNS, Phase2Config, get_default_config
from modules.derived_inventory import build_ups_inventory

NDC = "12345000602"
SKU = "12345-006-02"


def _logger():
    logger = logging.getLogger("test_pickticket_status_filter")
    logger.addHandler(logging.NullHandler())
    return logger


def _config(included=None) -> Phase2Config:
    return Phase2Config(
        derived_workbook_name="Derived_Data.xlsx",
        open_order_excluded_statuses=("Pick Completed", "Loaded"),
        sku_delimiter="-",
        sku_segment_widths=(5, 3, 2),
        ndc_segment_widths=(5, 4, 2),
        open_order_included_statuses=(
            included
            if included is not None
            else (
                "In Distribution",
                "In Picking",
                "Ready for Pickroot Creation",
                "Ready for Wave Creation",
            )
        ),
    )


def _inventory(qty: int = 100) -> pd.DataFrame:
    return pd.DataFrame(
        {
            INVENTORY_COLUMNS["ndc"]: [NDC],
            INVENTORY_COLUMNS["inventory"]: [qty],
            INVENTORY_COLUMNS["hold_codes"]: [""],
        }
    )


def _open_orders(statuses: list[str], qty: int = 10) -> pd.DataFrame:
    return pd.DataFrame(
        {
            OPEN_ORDER_COLUMNS["sku"]: [SKU] * len(statuses),
            OPEN_ORDER_COLUMNS["total"]: [qty] * len(statuses),
            OPEN_ORDER_COLUMNS["pickticket_status"]: statuses,
        }
    )


def _total(statuses: list[str], config: Phase2Config | None = None) -> float:
    result = build_ups_inventory(
        _inventory(),
        _open_orders(statuses),
        config or _config(),
        _logger(),
    )
    row = result.dataframe.loc[result.dataframe["NDC"] == NDC].iloc[0]
    return float(row["Total"])


class DefaultConfigTests(unittest.TestCase):
    def test_default_config_lists_all_four_statuses(self):
        included = {
            s.upper() for s in get_default_config().phase2.open_order_included_statuses
        }
        self.assertEqual(
            included,
            {
                "IN DISTRIBUTION",
                "IN PICKING",
                "READY FOR PICKROOT CREATION",
                "READY FOR WAVE CREATION",
            },
        )


class IncludedStatusTests(unittest.TestCase):
    def test_existing_statuses_are_counted(self):
        self.assertEqual(_total(["In Distribution"]), 10)
        self.assertEqual(_total(["In Picking"]), 10)

    def test_new_statuses_are_counted(self):
        self.assertEqual(_total(["Ready for Pickroot Creation"]), 10)
        self.assertEqual(_total(["Ready for Wave Creation"]), 10)

    def test_all_four_statuses_sum_together(self):
        self.assertEqual(
            _total(
                [
                    "In Distribution",
                    "In Picking",
                    "Ready for Pickroot Creation",
                    "Ready for Wave Creation",
                ]
            ),
            40,
        )

    def test_matching_is_case_and_whitespace_insensitive(self):
        self.assertEqual(_total(["  ready   for WAVE creation "]), 10)
        self.assertEqual(_total(["IN PICKING"]), 10)


class ExcludedStatusTests(unittest.TestCase):
    def test_pick_completed_is_ignored(self):
        self.assertEqual(_total(["Pick Completed"]), 0)

    def test_loaded_is_ignored(self):
        self.assertEqual(_total(["Loaded"]), 0)

    def test_unknown_status_is_ignored(self):
        self.assertEqual(_total(["Some New Status"]), 0)

    def test_blank_status_is_ignored(self):
        self.assertEqual(_total([""]), 0)

    def test_mixed_rows_only_count_included(self):
        self.assertEqual(
            _total(["In Picking", "Pick Completed", "Ready for Wave Creation"]), 20
        )


class UpsInventoryTests(unittest.TestCase):
    def test_ups_inventory_nets_only_included_statuses(self):
        result = build_ups_inventory(
            _inventory(100),
            _open_orders(["In Picking", "Ready for Pickroot Creation", "Pick Completed"]),
            _config(),
            _logger(),
        )
        row = result.dataframe.loc[result.dataframe["NDC"] == NDC].iloc[0]
        self.assertEqual(float(row["Total"]), 20)
        self.assertEqual(float(row["UPS Inventory"]), 80)


class LegacyFallbackTests(unittest.TestCase):
    """An empty allow-list must preserve the original exclusion behaviour."""

    def test_empty_allow_list_falls_back_to_exclusions(self):
        config = _config(included=())
        self.assertEqual(_total(["Anything Else"], config), 10)
        self.assertEqual(_total(["Pick Completed"], config), 0)


if __name__ == "__main__":
    unittest.main()
