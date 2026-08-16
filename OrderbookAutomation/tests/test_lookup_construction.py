"""Tests for canonical master "Lookup" column construction.

Covers the structural fix to modules/master_builder.py:
- _ensure_lookup() always (re)computes the canonical Lookup from the
  orderbook's own "NDC Code" + "Sold-to party Name", regardless of whether a
  "Lookup" column already exists on the incoming dataframe.
- Source workbooks that happen to contain their own "Lookup" column (Sales
  Summary, Awards) must never have that value copied into the master
  dataframe / overwrite the canonical Lookup.
- Exactly one "Lookup" column exists on the final master dataframe; no
  "Lookup_x"/"Lookup_y"/"Lookup_source" columns are ever produced.
- NDC and customer-name normalization variants used to build Lookup produce
  identical keys, and original business columns are never mutated.
"""
import logging
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from modules.master_builder import _ensure_lookup, build_master_workbook


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_lookup_construction")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


class TestEnsureLookupCanonicalConstruction(unittest.TestCase):
    def test_no_existing_lookup_column_is_created(self) -> None:
        df = pd.DataFrame(
            {
                "NDC Code": ["64380-020-101"],
                "Sold-to party Name": ["Express Scripts"],
            }
        )
        result = _ensure_lookup(df, logger=_silent_logger())
        self.assertIn("Lookup", result.columns)
        self.assertEqual(result.loc[0, "Lookup"], "64380020101EXPRESS SCRIPTS")

    def test_existing_foreign_lookup_column_is_recalculated_from_canonical_fields(self) -> None:
        # Simulate a "Lookup" column that leaked in from a source workbook
        # (e.g. Sales Summary/Awards) with a completely unrelated value.
        df = pd.DataFrame(
            {
                "NDC Code": ["64380020101"],
                "Sold-to party Name": ["Express Scripts"],
                "Lookup": ["SOME_FOREIGN_VALUE_FROM_ANOTHER_FILE"],
            }
        )
        result = _ensure_lookup(df, logger=_silent_logger())
        self.assertEqual(result.loc[0, "Lookup"], "64380020101EXPRESS SCRIPTS")
        self.assertNotEqual(result.loc[0, "Lookup"], "SOME_FOREIGN_VALUE_FROM_ANOTHER_FILE")

    def test_original_columns_are_not_mutated(self) -> None:
        df = pd.DataFrame(
            {
                "NDC Code": ["64380-020-101"],
                "Sold-to party Name": [" express   scripts "],
            }
        )
        result = _ensure_lookup(df, logger=_silent_logger())
        self.assertEqual(result.loc[0, "NDC Code"], "64380-020-101")
        self.assertEqual(result.loc[0, "Sold-to party Name"], " express   scripts ")

    def test_missing_ndc_column_yields_blank_lookup_without_error(self) -> None:
        df = pd.DataFrame({"Sold-to party Name": ["Express Scripts"]})
        result = _ensure_lookup(df, logger=_silent_logger())
        self.assertIn("Lookup", result.columns)
        self.assertTrue(result["Lookup"].isna().all())

    def test_missing_sold_to_party_name_column_yields_blank_lookup_without_error(self) -> None:
        df = pd.DataFrame({"NDC Code": ["64380020101"]})
        result = _ensure_lookup(df, logger=_silent_logger())
        self.assertIn("Lookup", result.columns)
        self.assertTrue(result["Lookup"].isna().all())

    def test_missing_ndc_value_on_individual_row_yields_partial_lookup_for_that_row(self) -> None:
        # Pre-existing formula behavior (unchanged by this fix): each side is
        # independently fillna(""), so a missing NDC on one row still yields
        # a non-blank partial Lookup (customer-only) for that row, while a
        # fully populated row yields the full canonical Lookup.
        df = pd.DataFrame(
            {
                "NDC Code": [None, "64380020101"],
                "Sold-to party Name": ["Express Scripts", "Express Scripts"],
            }
        )
        result = _ensure_lookup(df, logger=_silent_logger())
        self.assertEqual(result.loc[0, "Lookup"], "EXPRESS SCRIPTS")
        self.assertEqual(result.loc[1, "Lookup"], "64380020101EXPRESS SCRIPTS")

    def test_dashed_and_undashed_ndc_produce_same_lookup(self) -> None:
        dashed = pd.DataFrame({"NDC Code": ["64380-0201-01"], "Sold-to party Name": ["Express Scripts"]})
        undashed = pd.DataFrame({"NDC Code": ["64380020101"], "Sold-to party Name": ["Express Scripts"]})
        lookup_dashed = _ensure_lookup(dashed, logger=_silent_logger()).loc[0, "Lookup"]
        lookup_undashed = _ensure_lookup(undashed, logger=_silent_logger()).loc[0, "Lookup"]
        self.assertEqual(lookup_dashed, lookup_undashed)

    def test_customer_name_case_and_whitespace_variants_produce_same_lookup(self) -> None:
        variants = ["Express Scripts", "express scripts", " EXPRESS   SCRIPTS "]
        lookups = set()
        for variant in variants:
            df = pd.DataFrame({"NDC Code": ["64380020101"], "Sold-to party Name": [variant]})
            lookups.add(_ensure_lookup(df, logger=_silent_logger()).loc[0, "Lookup"])
        self.assertEqual(lookups, {"64380020101EXPRESS SCRIPTS"})

    def test_no_duplicate_lookup_columns_produced(self) -> None:
        df = pd.DataFrame(
            {
                "NDC Code": ["64380020101"],
                "Sold-to party Name": ["Express Scripts"],
                "Lookup": ["stale"],
            }
        )
        result = _ensure_lookup(df, logger=_silent_logger())
        lookup_like_columns = [column for column in result.columns if column.startswith("Lookup")]
        self.assertEqual(lookup_like_columns, ["Lookup"])


class TestSourceLookupDoesNotOverwriteMaster(unittest.TestCase):
    """End-to-end coverage through build_master_workbook() confirming that
    Sales Summary's and Awards' own "Lookup" columns never leak into or
    overwrite the master dataframe's canonical Lookup."""

    def setUp(self) -> None:
        self.logger = _silent_logger()
        self.tmpdir = TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.output_path = Path(self.tmpdir.name) / "Business_Master_Data.xlsx"

    def _orderbook_df(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "Sales Order No.": [1001],
                "NDC Code": ["64380020101"],
                "Sold-to party Name": ["Express Scripts"],
                "PackSize(MOQ)": [24],
            }
        )

    def test_sales_summary_lookup_does_not_overwrite_master_lookup(self) -> None:
        sales_summary_df = pd.DataFrame(
            {
                "Sales Order No.": [1001],
                "NDC Code": ["64380020101"],
                "Sold-to party Name": ["Express Scripts"],
                "Lookup": ["FOREIGN_SALES_SUMMARY_LOOKUP_VALUE"],
                "Sales Order Qty": [24],
            }
        )
        result = build_master_workbook(
            self._orderbook_df(),
            {"sales_summary": sales_summary_df},
            self.output_path,
            logger=self.logger,
        )
        self.assertEqual(result.master_df.loc[0, "Lookup"], "64380020101EXPRESS SCRIPTS")

    def test_awards_lookup_does_not_overwrite_master_lookup(self) -> None:
        awards_df = pd.DataFrame(
            {
                "NDC": ["64380020101"],
                "Customer": ["Express Scripts"],
                "Lookup": ["FOREIGN_AWARDS_LOOKUP_VALUE"],
                "Award Type": ["Backup"],
            }
        )
        result = build_master_workbook(
            self._orderbook_df(),
            {"awards": awards_df},
            self.output_path,
            logger=self.logger,
        )
        self.assertEqual(result.master_df.loc[0, "Lookup"], "64380020101EXPRESS SCRIPTS")

    def test_final_master_has_exactly_one_lookup_column(self) -> None:
        sales_summary_df = pd.DataFrame(
            {
                "Sales Order No.": [1001],
                "NDC Code": ["64380020101"],
                "Sold-to party Name": ["Express Scripts"],
                "Lookup": ["FOREIGN_VALUE_1"],
            }
        )
        awards_df = pd.DataFrame(
            {
                "NDC": ["64380020101"],
                "Customer": ["Express Scripts"],
                "Lookup": ["FOREIGN_VALUE_2"],
            }
        )
        result = build_master_workbook(
            self._orderbook_df(),
            {"sales_summary": sales_summary_df, "awards": awards_df},
            self.output_path,
            logger=self.logger,
        )
        lookup_like_columns = [column for column in result.master_df.columns if column.startswith("Lookup")]
        self.assertEqual(lookup_like_columns, ["Lookup"])
        self.assertNotIn("Lookup_x", result.master_df.columns)
        self.assertNotIn("Lookup_y", result.master_df.columns)
        self.assertNotIn("Lookup_source", result.master_df.columns)


if __name__ == "__main__":
    unittest.main()
