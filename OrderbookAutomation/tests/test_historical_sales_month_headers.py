"""Tests for the dynamic historical-sales month header/data alignment
(modules/historical_sales.py, modules/phase4_manager.py).

Business rule under test:

- The three historical month columns AND their Excel headers are both
  dynamically determined from the reporting/processing month -- the
  previous 3 COMPLETED months (never the current month).
- Header text and underlying values must refer to the exact same
  calendar month (matched by YEAR + MONTH, not column position/name).
- The final client-facing Summary sheet (POB.xlsx) must NOT hardcode
  "Apr"/"May"/"Jun"; those are only used when they are genuinely the
  correct previous 3 months for the run.
- Average must use the exact floating-point mean of the 3 selected
  months (no rounding/truncation), skipping blank months.
- A missing historical month must be left blank, never substituted.
"""

from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.historical_sales import (  # noqa: E402
    build_historical_sales,
    month_label,
    previous_n_months,
)
from modules.phase4_manager import _summary_reference_columns, _to_reference_summary_dataframe  # noqa: E402


def _logger():
    logger = logging.getLogger("test_historical_sales_month_headers")
    logger.addHandler(logging.NullHandler())
    return logger


def _strend_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


class TestPreviousNMonths(unittest.TestCase):
    """Step 11 sample cases + Step 9 year boundary cases."""

    def test_may_2026_selects_feb_mar_apr(self):
        months = previous_n_months(2026, 5, count=3)
        self.assertEqual(months, [(2026, 2), (2026, 3), (2026, 4)])
        labels = [month_label(m) for _, m in months]
        self.assertEqual(labels, ["Feb", "Mar", "Apr"])

    def test_august_2026_selects_may_jun_jul(self):
        months = previous_n_months(2026, 8, count=3)
        self.assertEqual(months, [(2026, 5), (2026, 6), (2026, 7)])
        labels = [month_label(m) for _, m in months]
        self.assertEqual(labels, ["May", "Jun", "Jul"])
        # Current month (August) must never appear.
        self.assertNotIn("Aug", labels)

    def test_january_2026_year_boundary_selects_oct_nov_dec_2025(self):
        months = previous_n_months(2026, 1, count=3)
        self.assertEqual(months, [(2025, 10), (2025, 11), (2025, 12)])
        labels = [month_label(m) for _, m in months]
        self.assertEqual(labels, ["Oct", "Nov", "Dec"])

    def test_february_2026_year_boundary_selects_nov_dec_jan(self):
        months = previous_n_months(2026, 2, count=3)
        self.assertEqual(months, [(2025, 11), (2025, 12), (2026, 1)])
        labels = [month_label(m) for _, m in months]
        self.assertEqual(labels, ["Nov", "Dec", "Jan"])

    def test_march_2026_year_boundary_selects_dec_jan_feb(self):
        months = previous_n_months(2026, 3, count=3)
        self.assertEqual(months, [(2025, 12), (2026, 1), (2026, 2)])
        labels = [month_label(m) for _, m in months]
        self.assertEqual(labels, ["Dec", "Jan", "Feb"])


class TestBuildHistoricalSalesAlignment(unittest.TestCase):
    """Header/data alignment and year-disambiguation (Step 6)."""

    def test_header_and_data_use_same_year_not_first_matching_name(self):
        # Strend contains BOTH Jul-25 and Jul-26; report period selects the
        # true previous-3-months for an October 2026 run: Jul/Aug/Sep 2026.
        strend = _strend_df(
            [
                {"Lookup": "KEY1", "Jul-25": 999, "Jul-26": 111, "Aug-26": 222, "Sep-26": 333},
            ]
        )
        result = build_historical_sales(strend, pd.Series(["KEY1"]), 2026, 10, _logger())
        self.assertEqual(result.previous_month_labels, ("Jul", "Aug", "Sep"))
        row = result.dataframe.iloc[0]
        # Must pick Jul-26 (111), not Jul-25 (999).
        self.assertEqual(row["Jul"], 111)
        self.assertEqual(row["Aug"], 222)
        self.assertEqual(row["Sep"], 333)

    def test_missing_month_left_blank_not_substituted(self):
        strend = _strend_df(
            [
                {"Lookup": "KEY1", "May-26": 100, "Jul-26": 300},  # Jun-26 missing
            ]
        )
        result = build_historical_sales(strend, pd.Series(["KEY1"]), 2026, 8, _logger())
        self.assertEqual(result.previous_month_labels, ("May", "Jun", "Jul"))
        self.assertIsNone(result.previous_month_headers[1])  # Jun missing
        row = result.dataframe.iloc[0]
        self.assertEqual(row["May"], 100)
        self.assertTrue(pd.isna(row["Jun"]))
        self.assertEqual(row["Jul"], 300)
        # Average must skip the blank month: (100+300)/2 = 200.0 exactly.
        self.assertEqual(row["Average"], 200.0)

    def test_average_is_exact_float_not_rounded(self):
        strend = _strend_df(
            [{"Lookup": "KEY1", "May-26": 100, "Jun-26": 101, "Jul-26": 103}]
        )
        result = build_historical_sales(strend, pd.Series(["KEY1"]), 2026, 8, _logger())
        row = result.dataframe.iloc[0]
        self.assertAlmostEqual(row["Average"], 101.33333333333333, places=10)
        self.assertNotEqual(row["Average"], 101)  # not rounded/truncated

    def test_average_all_blank_preserves_na(self):
        strend = _strend_df([{"Lookup": "KEY1"}])
        result = build_historical_sales(strend, pd.Series(["KEY1"]), 2026, 8, _logger())
        row = result.dataframe.iloc[0]
        self.assertTrue(pd.isna(row["Average"]))


class TestSummaryReferenceHeadersDynamic(unittest.TestCase):
    """Step 7: final POB.xlsx Summary headers must be dynamic, not a
    hardcoded Apr/May/Jun."""

    def test_may_processing_month_produces_feb_mar_apr_headers(self):
        month_labels = ("Feb", "Mar", "Apr")
        columns = _summary_reference_columns(month_labels)
        self.assertIn("Feb", columns)
        self.assertIn("Mar", columns)
        self.assertIn("Apr", columns)
        self.assertNotIn("May", columns)
        self.assertNotIn("Jun", columns)
        # Order: oldest -> newest -> Avg
        idx_feb, idx_mar, idx_apr, idx_avg = (
            columns.index("Feb"),
            columns.index("Mar"),
            columns.index("Apr"),
            columns.index("Avg"),
        )
        self.assertLess(idx_feb, idx_mar)
        self.assertLess(idx_mar, idx_apr)
        self.assertLess(idx_apr, idx_avg)

    def test_august_processing_month_produces_may_jun_jul_headers(self):
        month_labels = ("May", "Jun", "Jul")
        columns = _summary_reference_columns(month_labels)
        self.assertIn("May", columns)
        self.assertIn("Jun", columns)
        self.assertIn("Jul", columns)
        self.assertNotIn("Apr", columns)  # no leftover static assumption

    def test_january_processing_month_produces_oct_nov_dec_headers(self):
        month_labels = ("Oct", "Nov", "Dec")
        columns = _summary_reference_columns(month_labels)
        self.assertIn("Oct", columns)
        self.assertIn("Nov", columns)
        self.assertIn("Dec", columns)
        self.assertNotIn("Apr", columns)
        self.assertNotIn("May", columns)
        self.assertNotIn("Jun", columns)

    def test_to_reference_summary_dataframe_uses_dynamic_headers_with_correct_data(self):
        month_labels = ("May", "Jun", "Jul")
        summary_df = pd.DataFrame(
            [
                {
                    "Material Description": "Widget",
                    "Sold-to party Name": "ACME",
                    "Lookup": "KEY1",
                    "NDC Code": "123456789",
                    "Max of UPS Inventory": 10,
                    "Sum of Sales Order Qty": 5,
                    "Max of Sales Qty MTD": 2,
                    "Max of Forecast Qty": 3,
                    "Avinash/Krishna Comments": "note",
                    "May": 100,
                    "Jun": 120,
                    "Jul": 140,
                    "Average": 120.0,
                    "Buying Group": "BG1",
                    "Award Type": "AT1",
                    "SC Comments": "SC1",
                }
            ]
        )
        result = _to_reference_summary_dataframe(summary_df, month_labels)
        self.assertIn("May", result.columns)
        self.assertIn("Jun", result.columns)
        self.assertIn("Jul", result.columns)
        self.assertEqual(result.iloc[0]["May"], 100)
        self.assertEqual(result.iloc[0]["Jun"], 120)
        self.assertEqual(result.iloc[0]["Jul"], 140)
        self.assertEqual(result.iloc[0]["Avg"], 120.0)
        # No stray hardcoded Apr column when May/Jun/Jul are the real months.
        self.assertNotIn("Apr", result.columns)


if __name__ == "__main__":
    unittest.main()
