"""Tests for the Hold Codes eligibility filter applied to the UPS Inventory
calculation (modules/derived_inventory.py, modules/utils.py).

Business rule under test:

- ONLY Daily Inventory rows with a BLANK Hold Codes value are eligible to
  contribute inventory quantity to the UPS Inventory calculation.
- Blank includes: actual NaN/None, empty string, and whitespace-only
  strings (spaces/tabs/newlines with no real content).
- Any other, non-blank text (e.g. "HOLD", "QC", "DAMAGED") excludes the row.
- The filter must NOT alter Orderbook or Open Order Summary row counts.
"""

from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import INVENTORY_COLUMNS, OPEN_ORDER_COLUMNS, Phase2Config  # noqa: E402
from modules.derived_inventory import build_ups_inventory  # noqa: E402
from modules.utils import is_blank_hold_code  # noqa: E402


def _logger():
    logger = logging.getLogger("test_hold_code_filter")
    logger.addHandler(logging.NullHandler())
    return logger


def _phase2_config() -> Phase2Config:
    return Phase2Config(
        derived_workbook_name="Derived_Data.xlsx",
        open_order_excluded_statuses=("CANCELLED",),
        sku_delimiter="-",
        sku_segment_widths=("5", "4"),
        ndc_segment_widths=("5", "4"),
    )


def _open_orders(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


class TestIsBlankHoldCode(unittest.TestCase):
    def test_nan_is_blank(self):
        self.assertTrue(is_blank_hold_code(np.nan))

    def test_none_is_blank(self):
        self.assertTrue(is_blank_hold_code(None))

    def test_empty_string_is_blank(self):
        self.assertTrue(is_blank_hold_code(""))

    def test_whitespace_only_is_blank(self):
        self.assertTrue(is_blank_hold_code("   "))
        self.assertTrue(is_blank_hold_code("\t\n  "))

    def test_hold_is_not_blank(self):
        self.assertFalse(is_blank_hold_code("HOLD"))

    def test_qc_is_not_blank(self):
        self.assertFalse(is_blank_hold_code("QC"))

    def test_damaged_is_not_blank(self):
        self.assertFalse(is_blank_hold_code("DAMAGED"))


class TestUpsInventoryHoldCodeFilter(unittest.TestCase):
    def setUp(self):
        self.logger = _logger()
        self.config = _phase2_config()
        self.open_orders_df = _open_orders(
            [
                {
                    OPEN_ORDER_COLUMNS["sku"]: "12345-6789",
                    OPEN_ORDER_COLUMNS["total"]: 10,
                    OPEN_ORDER_COLUMNS["pickticket_status"]: "OPEN",
                },
            ]
        )

    def _inventory(self, hold_codes: list, quantities: list, ndcs: list) -> pd.DataFrame:
        return pd.DataFrame(
            {
                INVENTORY_COLUMNS["ndc"]: ndcs,
                INVENTORY_COLUMNS["inventory"]: quantities,
                INVENTORY_COLUMNS["hold_codes"]: hold_codes,
            }
        )

    def test_mixed_blank_and_nonblank_rows_only_blank_contribute(self):
        inventory_df = self._inventory(
            hold_codes=[np.nan, "", "   ", "HOLD", "QC"],
            quantities=[100, 50, 25, 999, 999],
            ndcs=["123456789"] * 5,
        )
        result = build_ups_inventory(inventory_df, self.open_orders_df, self.config, self.logger)
        self.assertEqual(result.total_inventory_rows, 5)
        self.assertEqual(result.blank_hold_code_rows, 3)
        self.assertEqual(result.excluded_hold_code_rows, 2)
        row = result.dataframe.loc[result.dataframe["NDC"] == "123456789"].iloc[0]
        self.assertEqual(row["Inventory"], 175)  # 100 + 50 + 25, excludes 999+999

    def test_all_blank_result_unchanged(self):
        inventory_df = self._inventory(
            hold_codes=[np.nan, "", "  "],
            quantities=[10, 20, 30],
            ndcs=["999999999"] * 3,
        )
        result = build_ups_inventory(inventory_df, self.open_orders_df, self.config, self.logger)
        self.assertEqual(result.excluded_hold_code_rows, 0)
        self.assertEqual(result.blank_hold_code_rows, 3)
        row = result.dataframe.loc[result.dataframe["NDC"] == "999999999"].iloc[0]
        self.assertEqual(row["Inventory"], 60)

    def test_all_populated_inventory_contribution_zero(self):
        inventory_df = self._inventory(
            hold_codes=["HOLD", "QC", "DAMAGED"],
            quantities=[10, 20, 30],
            ndcs=["111111111"] * 3,
        )
        result = build_ups_inventory(inventory_df, self.open_orders_df, self.config, self.logger)
        self.assertEqual(result.blank_hold_code_rows, 0)
        self.assertEqual(result.excluded_hold_code_rows, 3)
        # NDC has no eligible inventory rows left, so it should not appear
        # with a positive inventory contribution from this NDC.
        matching = result.dataframe.loc[result.dataframe["NDC"] == "111111111"]
        if not matching.empty:
            self.assertEqual(matching.iloc[0]["Inventory"], 0)

    def test_orderbook_row_count_unaffected(self):
        # Orderbook is not part of this calculation path at all; confirm the
        # open order summary (a stand-in transactional source here) keeps
        # its row count irrespective of inventory-side filtering.
        inventory_df = self._inventory(
            hold_codes=["HOLD"],
            quantities=[10],
            ndcs=["123456789"],
        )
        before_rows = len(self.open_orders_df)
        build_ups_inventory(inventory_df, self.open_orders_df, self.config, self.logger)
        self.assertEqual(len(self.open_orders_df), before_rows)

    def test_ndc_aggregation_after_filtering(self):
        inventory_df = self._inventory(
            hold_codes=[np.nan, "HOLD", "", "QC"],
            quantities=[50, 999, 25, 999],
            ndcs=["555555555", "555555555", "666666666", "666666666"],
        )
        result = build_ups_inventory(inventory_df, self.open_orders_df, self.config, self.logger)
        row_555 = result.dataframe.loc[result.dataframe["NDC"] == "555555555"].iloc[0]
        row_666 = result.dataframe.loc[result.dataframe["NDC"] == "666666666"].iloc[0]
        self.assertEqual(row_555["Inventory"], 50)
        self.assertEqual(row_666["Inventory"], 25)
        self.assertEqual(result.unique_ndcs_after_filter, 2)

    def test_missing_hold_codes_column_treats_all_as_eligible(self):
        inventory_df = pd.DataFrame(
            {
                INVENTORY_COLUMNS["ndc"]: ["123456789"],
                INVENTORY_COLUMNS["inventory"]: [42],
            }
        )
        result = build_ups_inventory(inventory_df, self.open_orders_df, self.config, self.logger)
        self.assertEqual(result.blank_hold_code_rows, 1)
        self.assertEqual(result.excluded_hold_code_rows, 0)
        row = result.dataframe.loc[result.dataframe["NDC"] == "123456789"].iloc[0]
        self.assertEqual(row["Inventory"], 42)


if __name__ == "__main__":
    unittest.main()
