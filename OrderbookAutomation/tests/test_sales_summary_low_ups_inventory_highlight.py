"""Tests for the low UPS Inventory yellow highlight on Sales_Summary.xlsx.

Business rule under test:

    On the Sales Summary sheet, when "Max of UPS Inventory" < 10,000 that
    single cell is filled yellow. Only that cell is filled -- never the
    whole row, and never any other column.

This rule was MOVED off the client-facing POB.xlsx "UPS Inventory"
column (see test_moq_row_highlight.py, which pins that POB.xlsx no
longer highlights it).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd
from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.business_rules import LOW_UPS_INVENTORY_THRESHOLD  # noqa: E402
from modules.report_formatter import (  # noqa: E402
    FILL_LOW_INVENTORY_YELLOW,
    apply_low_ups_inventory_formatting,
    write_dataframe_sheet,
)

YELLOW = FILL_LOW_INVENTORY_YELLOW.fgColor.rgb


def _fill_rgb(cell):
    fill = cell.fill
    if fill is None or fill.fill_type != "solid":
        return None
    return fill.fgColor.rgb


def _build_sheet(values: list) -> tuple:
    workbook = Workbook()
    df = pd.DataFrame(
        {
            "Material Description": [f"Product {i}" for i in range(len(values))],
            "Sold-to party Name": ["Customer"] * len(values),
            "Max of UPS Inventory": values,
            "Sum of Sales Order Qty": [100] * len(values),
        }
    )
    worksheet = write_dataframe_sheet(workbook, "Sales Summary", df)
    count = apply_low_ups_inventory_formatting(worksheet)
    header = {str(c.value): c.column for c in worksheet[1]}
    return worksheet, header, count


class TestSalesSummaryLowUpsInventoryHighlight(unittest.TestCase):
    def test_below_threshold_is_highlighted(self):
        worksheet, header, count = _build_sheet([9_999])
        cell = worksheet.cell(row=2, column=header["Max of UPS Inventory"])
        self.assertEqual(_fill_rgb(cell), YELLOW)
        self.assertEqual(count, 1)

    def test_at_threshold_is_not_highlighted(self):
        worksheet, header, count = _build_sheet([LOW_UPS_INVENTORY_THRESHOLD])
        cell = worksheet.cell(row=2, column=header["Max of UPS Inventory"])
        self.assertIsNone(_fill_rgb(cell))
        self.assertEqual(count, 0)

    def test_above_threshold_is_not_highlighted(self):
        worksheet, header, count = _build_sheet([25_000])
        cell = worksheet.cell(row=2, column=header["Max of UPS Inventory"])
        self.assertIsNone(_fill_rgb(cell))
        self.assertEqual(count, 0)

    def test_zero_is_highlighted(self):
        worksheet, header, count = _build_sheet([0])
        cell = worksheet.cell(row=2, column=header["Max of UPS Inventory"])
        self.assertEqual(_fill_rgb(cell), YELLOW)
        self.assertEqual(count, 1)

    def test_only_the_ups_inventory_cell_is_filled(self):
        worksheet, header, _ = _build_sheet([500])
        for name, idx in header.items():
            if name == "Max of UPS Inventory":
                continue
            self.assertIsNone(
                _fill_rgb(worksheet.cell(row=2, column=idx)),
                f"'{name}' must not be highlighted",
            )

    def test_blank_and_non_numeric_values_are_skipped(self):
        worksheet, header, count = _build_sheet([None, "N/A"])
        column = header["Max of UPS Inventory"]
        self.assertIsNone(_fill_rgb(worksheet.cell(row=2, column=column)))
        self.assertIsNone(_fill_rgb(worksheet.cell(row=3, column=column)))
        self.assertEqual(count, 0)

    def test_only_qualifying_rows_are_highlighted(self):
        worksheet, header, count = _build_sheet([100, 50_000, 9_999, 10_001])
        column = header["Max of UPS Inventory"]
        self.assertEqual(_fill_rgb(worksheet.cell(row=2, column=column)), YELLOW)
        self.assertIsNone(_fill_rgb(worksheet.cell(row=3, column=column)))
        self.assertEqual(_fill_rgb(worksheet.cell(row=4, column=column)), YELLOW)
        self.assertIsNone(_fill_rgb(worksheet.cell(row=5, column=column)))
        self.assertEqual(count, 2)

    def test_missing_column_is_a_no_op(self):
        workbook = Workbook()
        df = pd.DataFrame({"Material Description": ["Product"], "Sum of Sales Order Qty": [10]})
        worksheet = write_dataframe_sheet(workbook, "Sales Summary", df)
        self.assertEqual(apply_low_ups_inventory_formatting(worksheet), 0)

    def test_column_is_located_by_header_not_position(self):
        # Reordering columns must not change which cells get highlighted.
        workbook = Workbook()
        df = pd.DataFrame(
            {
                "Max of UPS Inventory": [500],
                "Material Description": ["Product"],
                "Sum of Sales Order Qty": [10],
            }
        )
        worksheet = write_dataframe_sheet(workbook, "Sales Summary", df)
        apply_low_ups_inventory_formatting(worksheet)
        header = {str(c.value): c.column for c in worksheet[1]}
        self.assertEqual(_fill_rgb(worksheet.cell(row=2, column=header["Max of UPS Inventory"])), YELLOW)
        self.assertIsNone(_fill_rgb(worksheet.cell(row=2, column=header["Material Description"])))


if __name__ == "__main__":
    unittest.main()
