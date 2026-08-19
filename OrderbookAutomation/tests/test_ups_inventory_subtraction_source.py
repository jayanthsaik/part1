"""Regression tests pinning the measure used in the UPS Inventory
subtraction (modules/derived_inventory.py).

Business rule under test:

    SUM(Daily Inventory["Inventory"])
    - SUM(Open Order Summary[" Total "])
    = UPS Inventory

The derived dataframe exposes the Open Order side under the internal
column label "Allocated". That label is HISTORICAL/INTERNAL ONLY: it is
the sum of Open Order Summary's " Total " column, NOT the Daily
Inventory "Allocated Quantity" column. These tests exist to prevent that
naming collision from being "fixed" by silently swapping in the wrong
source measure.

Explicitly proven here:

- Daily Inventory "Allocated Quantity" is NOT used in the subtraction.
- Daily Inventory "Actual Quantity" is NOT used in the subtraction.
- Open Order Summary " Total " IS used in the subtraction.
"""

from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import INVENTORY_COLUMNS, OPEN_ORDER_COLUMNS, Phase2Config  # noqa: E402
from modules.derived_inventory import build_ups_inventory  # noqa: E402

NDC = "123456789"
SKU = "12345-6789"


def _logger():
    logger = logging.getLogger("test_ups_inventory_subtraction_source")
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


def _inventory(inventory: float, allocated_quantity: float, actual_quantity: float) -> pd.DataFrame:
    """Daily Inventory row carrying all three quantity columns, so a test
    can prove which one actually drives the calculation."""
    return pd.DataFrame(
        {
            INVENTORY_COLUMNS["ndc"]: [NDC],
            INVENTORY_COLUMNS["inventory"]: [inventory],
            INVENTORY_COLUMNS["allocated_quantity"]: [allocated_quantity],
            INVENTORY_COLUMNS["actual_quantity"]: [actual_quantity],
            INVENTORY_COLUMNS["hold_codes"]: [""],
        }
    )


def _open_orders(total: float) -> pd.DataFrame:
    return pd.DataFrame(
        {
            OPEN_ORDER_COLUMNS["sku"]: [SKU],
            OPEN_ORDER_COLUMNS["total"]: [total],
            OPEN_ORDER_COLUMNS["pickticket_status"]: ["OPEN"],
        }
    )


def _ups_inventory(inventory_df: pd.DataFrame, open_orders_df: pd.DataFrame) -> float:
    result = build_ups_inventory(inventory_df, open_orders_df, _phase2_config(), _logger())
    row = result.dataframe.loc[result.dataframe["NDC"] == NDC].iloc[0]
    return float(row["UPS Inventory"])


class TestUpsInventorySubtractionSource(unittest.TestCase):
    def test_documented_scenario_uses_open_order_total(self):
        # Inventory 10,000 - Open Order Total 2,000 = 8,000.
        # If the Daily Inventory "Allocated Quantity" (9,000) were used
        # instead, this would be 1,000.
        ups = _ups_inventory(
            _inventory(inventory=10_000, allocated_quantity=9_000, actual_quantity=77_777),
            _open_orders(total=2_000),
        )
        self.assertEqual(ups, 8_000)

    def test_changing_daily_inventory_allocated_quantity_does_not_change_result(self):
        baseline = _ups_inventory(
            _inventory(inventory=10_000, allocated_quantity=9_000, actual_quantity=77_777),
            _open_orders(total=2_000),
        )
        changed = _ups_inventory(
            _inventory(inventory=10_000, allocated_quantity=1, actual_quantity=77_777),
            _open_orders(total=2_000),
        )
        self.assertEqual(baseline, changed)
        self.assertEqual(changed, 8_000)

    def test_changing_daily_inventory_actual_quantity_does_not_change_result(self):
        baseline = _ups_inventory(
            _inventory(inventory=10_000, allocated_quantity=9_000, actual_quantity=77_777),
            _open_orders(total=2_000),
        )
        changed = _ups_inventory(
            _inventory(inventory=10_000, allocated_quantity=9_000, actual_quantity=0),
            _open_orders(total=2_000),
        )
        self.assertEqual(baseline, changed)
        self.assertEqual(changed, 8_000)

    def test_changing_open_order_total_does_change_result(self):
        inventory_df = _inventory(inventory=10_000, allocated_quantity=9_000, actual_quantity=77_777)
        self.assertEqual(_ups_inventory(inventory_df, _open_orders(total=2_000)), 8_000)
        self.assertEqual(_ups_inventory(inventory_df, _open_orders(total=3_500)), 6_500)

    def test_zero_open_order_total_returns_full_inventory(self):
        ups = _ups_inventory(
            _inventory(inventory=10_000, allocated_quantity=9_000, actual_quantity=77_777),
            _open_orders(total=0),
        )
        self.assertEqual(ups, 10_000)

    def test_open_order_total_exceeding_inventory_is_negative(self):
        # No business rule currently clamps negative UPS Inventory.
        ups = _ups_inventory(
            _inventory(inventory=10_000, allocated_quantity=0, actual_quantity=0),
            _open_orders(total=12_000),
        )
        self.assertEqual(ups, -2_000)

    def test_formula_holds_across_a_range_of_totals(self):
        inventory_df = _inventory(inventory=10_000, allocated_quantity=9_000, actual_quantity=77_777)
        for total in (0, 1, 2_000, 9_999, 10_000, 25_000):
            with self.subTest(total=total):
                self.assertEqual(
                    _ups_inventory(inventory_df, _open_orders(total=total)),
                    10_000 - total,
                )

    def test_internal_allocated_column_holds_open_order_total(self):
        # The derived "Total" column is the SUM of Open Order " Total ",
        # never the Daily Inventory "Allocated Quantity" (9,000 here).
        result = build_ups_inventory(
            _inventory(inventory=10_000, allocated_quantity=9_000, actual_quantity=77_777),
            _open_orders(total=2_000),
            _phase2_config(),
            _logger(),
        )
        row = result.dataframe.loc[result.dataframe["NDC"] == NDC].iloc[0]
        self.assertEqual(float(row["Total"]), 2_000)
        self.assertEqual(float(row["Inventory"]), 10_000)
        self.assertEqual(float(row["UPS Inventory"]), float(row["Inventory"]) - float(row["Total"]))

    def test_hold_code_rows_excluded_from_inventory_side_only(self):
        # A held row's Inventory must not contribute; the Open Order Total
        # side remains governed by its own existing filtering rules.
        inventory_df = pd.DataFrame(
            {
                INVENTORY_COLUMNS["ndc"]: [NDC, NDC],
                INVENTORY_COLUMNS["inventory"]: [10_000, 5_000],
                INVENTORY_COLUMNS["allocated_quantity"]: [9_000, 9_000],
                INVENTORY_COLUMNS["actual_quantity"]: [77_777, 77_777],
                INVENTORY_COLUMNS["hold_codes"]: ["", "HOLD"],
            }
        )
        self.assertEqual(_ups_inventory(inventory_df, _open_orders(total=2_000)), 8_000)


if __name__ == "__main__":
    unittest.main()
