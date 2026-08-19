"""Tests for the MOQ Issue WHOLE-ROW yellow highlight in the final
Orderbook worksheet (modules/report_formatter.py), per the documented
manual process:

"...divide Sales Order Quantity by Pack Size (MOQ). Any lines with a
number after the decimal point are not in MOQ. Highlight these rows in
yellow. Once completed, remove the data entered in this column because
UPS Inventory will be populated here."

Business rule under test:

- Sales Order Qty / Pack Size (MOQ) not an exact multiple -> MOQ Issue.
- The ENTIRE Orderbook row is highlighted yellow (not just one cell).
- The MOQ Issue flag is computed independently from Sales Order Qty and
  Pack Size (MOQ) worksheet cells; since neither is a temporary/cleared
  calculation column in this worksheet, the flag/fill is stable and does
  not depend on any later UPS Inventory value.
- Blank/zero/non-numeric Pack Size or Sales Order Qty -> no highlight,
  no error.
- Independent of the Low_UPS_Inventory rule (which highlights only the
  UPS Inventory cell itself when < 10,000, not the entire row).
- Controlled Product (pink), Price Issue (orange), Cancel (red), and
  Hold (blue) rules remain unchanged.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd
from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.report_formatter import (  # noqa: E402
    FILL_CONTROLLED_PRODUCT_PINK,
    FILL_LOW_INVENTORY_YELLOW,
    _is_moq_issue,
    apply_business_rule_formatting,
    write_dataframe_sheet,
)


def _fill_rgb(cell) -> str | None:
    fill = cell.fill
    if fill is None or fill.fill_type is None:
        return None
    return str(fill.fgColor.rgb) if fill.fgColor is not None else None


def _row(sales_order_qty, pack_size, ups_inventory=50000):
    return {
        "Sales Order No.": "SO1",
        "Item No.": "1",
        "NDC Code": "123456789",
        "Material Description": "Widget",
        "UPS Inventory": ups_inventory,
        "Sales Order Qty": sales_order_qty,
        "Pack Size (MOQ)": pack_size,
        "Action": "",
        "Unit Price": 10,
        "WAC/BG price in EDI": 10,
    }


def _build_sheet(rows: list[dict], low_ups_inventory_flags=None):
    workbook = Workbook()
    df = pd.DataFrame(rows)
    worksheet = write_dataframe_sheet(workbook, "Orderbook", df)
    flags_df = df.copy()
    flags_df["Controlled_Product"] = False
    flags_df["Price_Issue"] = False
    flags_df["Low_UPS_Inventory"] = low_ups_inventory_flags if low_ups_inventory_flags is not None else [False] * len(rows)
    apply_business_rule_formatting(worksheet, flags_df)
    return worksheet, df


class TestIsMoqIssueUnit(unittest.TestCase):
    def test_48_over_24_no_issue(self):
        self.assertFalse(_is_moq_issue(48, 24))

    def test_50_over_24_is_issue(self):
        self.assertTrue(_is_moq_issue(50, 24))

    def test_72_over_24_no_issue(self):
        self.assertFalse(_is_moq_issue(72, 24))

    def test_75_over_24_is_issue(self):
        self.assertTrue(_is_moq_issue(75, 24))

    def test_pack_size_blank_no_issue(self):
        self.assertFalse(_is_moq_issue(50, None))

    def test_pack_size_zero_no_issue(self):
        self.assertFalse(_is_moq_issue(50, 0))

    def test_pack_size_non_numeric_no_issue(self):
        self.assertFalse(_is_moq_issue(50, "xyz"))


class TestMoqWholeRowHighlight(unittest.TestCase):
    def test_48_over_24_no_yellow(self):
        worksheet, df = _build_sheet([_row(48, 24)])
        header = {str(c.value): c.column for c in worksheet[1]}
        for column_index in header.values():
            self.assertIsNone(_fill_rgb(worksheet.cell(row=2, column=column_index)))

    def test_50_over_24_entire_row_yellow(self):
        worksheet, df = _build_sheet([_row(50, 24)])
        header = {str(c.value): c.column for c in worksheet[1]}
        for column_name, column_index in header.items():
            self.assertEqual(
                _fill_rgb(worksheet.cell(row=2, column=column_index)),
                FILL_LOW_INVENTORY_YELLOW.fgColor.rgb,
                f"Expected yellow on '{column_name}'",
            )

    def test_72_over_24_no_yellow(self):
        worksheet, df = _build_sheet([_row(72, 24)])
        header = {str(c.value): c.column for c in worksheet[1]}
        for column_index in header.values():
            self.assertIsNone(_fill_rgb(worksheet.cell(row=2, column=column_index)))

    def test_75_over_24_entire_row_yellow(self):
        worksheet, df = _build_sheet([_row(75, 24)])
        header = {str(c.value): c.column for c in worksheet[1]}
        for column_name, column_index in header.items():
            self.assertEqual(
                _fill_rgb(worksheet.cell(row=2, column=column_index)),
                FILL_LOW_INVENTORY_YELLOW.fgColor.rgb,
                f"Expected yellow on '{column_name}'",
            )

    def test_blank_pack_size_no_yellow(self):
        worksheet, df = _build_sheet([_row(50, None)])
        header = {str(c.value): c.column for c in worksheet[1]}
        for column_index in header.values():
            self.assertIsNone(_fill_rgb(worksheet.cell(row=2, column=column_index)))

    def test_zero_pack_size_no_yellow(self):
        worksheet, df = _build_sheet([_row(50, 0)])
        header = {str(c.value): c.column for c in worksheet[1]}
        for column_index in header.values():
            self.assertIsNone(_fill_rgb(worksheet.cell(row=2, column=column_index)))

    def test_non_numeric_pack_size_no_yellow(self):
        worksheet, df = _build_sheet([_row(50, "xyz")])
        header = {str(c.value): c.column for c in worksheet[1]}
        for column_index in header.values():
            self.assertIsNone(_fill_rgb(worksheet.cell(row=2, column=column_index)))

    def test_yellow_persists_after_ups_inventory_populated(self):
        # Sales Order Qty / Pack Size (MOQ) values that would be an MOQ
        # issue remain on the row (they are part of the final Orderbook
        # schema, not a cleared temporary column); UPS Inventory being
        # populated with a real value must not remove or bypass the
        # yellow fill that the MOQ Issue rule applies.
        worksheet, df = _build_sheet([_row(75, 24, ups_inventory=99999)])
        header = {str(c.value): c.column for c in worksheet[1]}
        ups_cell = worksheet.cell(row=2, column=header["UPS Inventory"])
        self.assertEqual(_fill_rgb(ups_cell), FILL_LOW_INVENTORY_YELLOW.fgColor.rgb)
        # Whole row still yellow.
        for column_index in header.values():
            self.assertEqual(_fill_rgb(worksheet.cell(row=2, column=column_index)), FILL_LOW_INVENTORY_YELLOW.fgColor.rgb)

    def test_temporary_recalculation_does_not_erase_prior_yellow(self):
        # Simulate re-running the formatting pass after the "temporary
        # calculation" concept -- re-invoking apply_business_rule_formatting
        # on the same worksheet/values must not lose the yellow fill.
        worksheet, df = _build_sheet([_row(75, 24)])
        header = {str(c.value): c.column for c in worksheet[1]}
        flags_df = df.copy()
        flags_df["Controlled_Product"] = False
        flags_df["Price_Issue"] = False
        flags_df["Low_UPS_Inventory"] = False
        apply_business_rule_formatting(worksheet, flags_df)  # re-apply
        for column_index in header.values():
            self.assertEqual(_fill_rgb(worksheet.cell(row=2, column=column_index)), FILL_LOW_INVENTORY_YELLOW.fgColor.rgb)

    def test_every_cell_in_moq_row_is_yellow(self):
        worksheet, df = _build_sheet([_row(75, 24)])
        header = {str(c.value): c.column for c in worksheet[1]}
        filled = {name: _fill_rgb(worksheet.cell(row=2, column=idx)) for name, idx in header.items()}
        for name, rgb in filled.items():
            self.assertEqual(rgb, FILL_LOW_INVENTORY_YELLOW.fgColor.rgb, f"'{name}' should be yellow")

    def test_non_moq_row_not_yellow(self):
        worksheet, df = _build_sheet([_row(48, 24)])
        header = {str(c.value): c.column for c in worksheet[1]}
        for name, idx in header.items():
            self.assertIsNone(_fill_rgb(worksheet.cell(row=2, column=idx)), f"'{name}' should not be yellow")

    def test_low_ups_inventory_is_not_highlighted_on_pob(self):
        # BUSINESS RULE: the low UPS Inventory yellow highlight was moved to
        # the Sales_Summary.xlsx "Max of UPS Inventory" column. Even when the
        # Low_UPS_Inventory flag is True, POB.xlsx must leave every cell --
        # including "UPS Inventory" -- unfilled when there is no MOQ issue
        # (48/24 is exact).
        worksheet, df = _build_sheet([_row(48, 24)], low_ups_inventory_flags=[True])
        header = {str(c.value): c.column for c in worksheet[1]}

        for name, idx in header.items():
            self.assertIsNone(
                _fill_rgb(worksheet.cell(row=2, column=idx)),
                f"'{name}' should not be highlighted on POB.xlsx",
            )

    def test_moq_row_still_yellow_when_low_ups_inventory_flag_set(self):
        # The MOQ whole-row highlight (75/24) is unaffected by the removal of
        # the low UPS Inventory rule; the entire row remains yellow.
        worksheet, df = _build_sheet([_row(75, 24)], low_ups_inventory_flags=[True])
        header = {str(c.value): c.column for c in worksheet[1]}
        for name, idx in header.items():
            self.assertEqual(_fill_rgb(worksheet.cell(row=2, column=idx)), FILL_LOW_INVENTORY_YELLOW.fgColor.rgb, name)

    def test_controlled_product_pink_takes_precedence_over_moq(self):
        workbook = Workbook()
        df = pd.DataFrame([_row(75, 24)])  # MOQ issue
        worksheet = write_dataframe_sheet(workbook, "Orderbook", df)
        flags_df = df.copy()
        flags_df["Controlled_Product"] = True
        flags_df["Price_Issue"] = False
        flags_df["Low_UPS_Inventory"] = False
        apply_business_rule_formatting(worksheet, flags_df)
        header = {str(c.value): c.column for c in worksheet[1]}
        for name, idx in header.items():
            self.assertEqual(_fill_rgb(worksheet.cell(row=2, column=idx)), FILL_CONTROLLED_PRODUCT_PINK.fgColor.rgb, name)

    def test_multiple_rows_only_moq_row_is_yellow(self):
        worksheet, df = _build_sheet([_row(48, 24), _row(50, 24), _row(72, 24)])
        header = {str(c.value): c.column for c in worksheet[1]}
        # Row 2 (48/24): no yellow.
        for idx in header.values():
            self.assertIsNone(_fill_rgb(worksheet.cell(row=2, column=idx)))
        # Row 3 (50/24): yellow.
        for idx in header.values():
            self.assertEqual(_fill_rgb(worksheet.cell(row=3, column=idx)), FILL_LOW_INVENTORY_YELLOW.fgColor.rgb)
        # Row 4 (72/24): no yellow.
        for idx in header.values():
            self.assertIsNone(_fill_rgb(worksheet.cell(row=4, column=idx)))


if __name__ == "__main__":
    unittest.main()
