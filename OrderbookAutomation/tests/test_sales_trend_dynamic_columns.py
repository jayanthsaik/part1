"""Tests for dynamic Strend.xlsx payload column resolution.

REGRESSION CONTEXT: the Sales Trend SourceSpec previously hardcoded the
headers " Jul-26 ", " July'26- Forecast " and " Avg Jan'26 to June'26 ".
Because the business rewrites those headers with every monthly export, the
following month's file merged NOTHING while still reporting success. These
tests pin the pattern-based resolution that replaced them.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.historical_sales import (
    find_forecast_header,
    find_latest_month_header,
    find_rolling_average_header,
    resolve_sales_trend_payload_columns,
)
from modules.master_builder import SOURCE_SPECS

# Headers as they actually appear in the July 2026 export.
JULY_COLUMNS = [
    "NDC Code",
    "Material Description",
    "Sold-to party Name",
    "Cust Group",
    " Cont ID ",
    "x",
    " May-26 ",
    " June-26 ",
    " Jul-26 ",
    " Open Order 7-29-2026 ",
    " July -26 ",
    " July'26- Forecast ",
    " Avg Jan'26 to June'26 ",
    " % ",
    " MTD-Target ",
]

# The same export one month later, with every period-specific header rewritten.
AUGUST_COLUMNS = [
    "NDC Code",
    "Material Description",
    "Sold-to party Name",
    "Cust Group",
    " Cont ID ",
    "x",
    " June-26 ",
    " Jul-26 ",
    " Aug-26 ",
    " Open Order 8-28-2026 ",
    " Aug'26- Forecast ",
    " Avg Feb'26 to July'26 ",
    " % ",
]


class LatestMonthTests(unittest.TestCase):
    def test_picks_newest_month(self):
        self.assertEqual(find_latest_month_header(JULY_COLUMNS), " Jul-26 ")

    def test_follows_the_export_forward(self):
        self.assertEqual(find_latest_month_header(AUGUST_COLUMNS), " Aug-26 ")

    def test_handles_year_rollover(self):
        columns = [" Nov-26 ", " Dec-26 ", " Jan-27 "]
        self.assertEqual(find_latest_month_header(columns), " Jan-27 ")

    def test_returns_none_when_no_month_columns(self):
        self.assertIsNone(find_latest_month_header(["NDC Code", "x"]))


class ForecastHeaderTests(unittest.TestCase):
    def test_finds_apostrophe_format(self):
        self.assertEqual(find_forecast_header(JULY_COLUMNS), " July'26- Forecast ")

    def test_finds_next_month_format(self):
        self.assertEqual(find_forecast_header(AUGUST_COLUMNS), " Aug'26- Forecast ")

    def test_can_be_pinned_to_a_period(self):
        self.assertEqual(find_forecast_header(JULY_COLUMNS, 2026, 7), " July'26- Forecast ")

    def test_pinning_to_absent_period_returns_none(self):
        self.assertIsNone(find_forecast_header(JULY_COLUMNS, 2026, 8))

    def test_tolerates_dash_and_case_variants(self):
        self.assertEqual(find_forecast_header([" Sep-26 forecast "]), " Sep-26 forecast ")

    def test_returns_none_when_absent(self):
        self.assertIsNone(find_forecast_header(["NDC Code", " Jul-26 "]))


class RollingAverageHeaderTests(unittest.TestCase):
    def test_finds_july_window(self):
        self.assertEqual(find_rolling_average_header(JULY_COLUMNS), " Avg Jan'26 to June'26 ")

    def test_finds_shifted_august_window(self):
        self.assertEqual(find_rolling_average_header(AUGUST_COLUMNS), " Avg Feb'26 to July'26 ")

    def test_accepts_average_spelling(self):
        self.assertEqual(
            find_rolling_average_header([" Average Jan-26 to Jun-26 "]),
            " Average Jan-26 to Jun-26 ",
        )

    def test_does_not_match_plain_month_column(self):
        self.assertIsNone(find_rolling_average_header([" Jul-26 ", "NDC Code"]))


class ResolvePayloadColumnsTests(unittest.TestCase):
    def test_july_resolves_to_the_previously_hardcoded_headers(self):
        """The exact three headers that used to be literals in master_builder."""
        self.assertEqual(
            resolve_sales_trend_payload_columns(JULY_COLUMNS),
            (" Jul-26 ", " July'26- Forecast ", " Avg Jan'26 to June'26 "),
        )

    def test_august_export_resolves_without_code_change(self):
        self.assertEqual(
            resolve_sales_trend_payload_columns(AUGUST_COLUMNS),
            (" Aug-26 ", " Aug'26- Forecast ", " Avg Feb'26 to July'26 "),
        )

    def test_missing_columns_are_omitted_not_invented(self):
        self.assertEqual(
            resolve_sales_trend_payload_columns(["NDC Code", "x", " Jul-26 "]),
            (" Jul-26 ",),
        )

    def test_no_matching_columns_returns_empty(self):
        self.assertEqual(resolve_sales_trend_payload_columns(["NDC Code", "x"]), ())

    def test_returned_headers_are_original_text(self):
        """Whitespace/case must be preserved so the merge can select them."""
        for header in resolve_sales_trend_payload_columns(JULY_COLUMNS):
            self.assertIn(header, JULY_COLUMNS)


class SourceSpecWiringTests(unittest.TestCase):
    def _sales_trend_spec(self):
        return next(spec for spec in SOURCE_SPECS if spec.dataframe_key == "sales_trend")

    def test_no_hardcoded_period_headers_remain(self):
        spec = self._sales_trend_spec()
        for column in spec.preferred_columns:
            self.assertNotIn("26", column, f"period-specific header still hardcoded: {column!r}")

    def test_resolver_is_attached(self):
        self.assertIsNotNone(self._sales_trend_spec().dynamic_columns_resolver)

    def test_resolve_preferred_columns_appends_dynamic_headers(self):
        spec = self._sales_trend_spec()
        resolved = spec.resolve_preferred_columns(JULY_COLUMNS)
        self.assertEqual(resolved[: len(spec.preferred_columns)], spec.preferred_columns)
        self.assertIn(" Jul-26 ", resolved)
        self.assertIn(" July'26- Forecast ", resolved)
        self.assertIn(" Avg Jan'26 to June'26 ", resolved)

    def test_resolve_preferred_columns_has_no_duplicates(self):
        resolved = self._sales_trend_spec().resolve_preferred_columns(JULY_COLUMNS)
        self.assertEqual(len(resolved), len(set(resolved)))

    def test_specs_without_resolver_are_unchanged(self):
        for spec in SOURCE_SPECS:
            if spec.dynamic_columns_resolver is None:
                self.assertEqual(spec.resolve_preferred_columns(["anything"]), spec.preferred_columns)


class RealWorkbookTests(unittest.TestCase):
    """Resolve against the actual Strend.xlsx when it is available."""

    def test_real_strend_resolves_three_payload_columns(self):
        path = Path(__file__).resolve().parents[1] / "input" / "Strend.xlsx"
        if not path.exists():
            self.skipTest("Strend.xlsx not present")
        columns = list(pd.read_excel(path, header=3).columns)
        resolved = resolve_sales_trend_payload_columns(columns)
        self.assertEqual(len(resolved), 3)
        for header in resolved:
            self.assertIn(header, columns)


if __name__ == "__main__":
    unittest.main()
