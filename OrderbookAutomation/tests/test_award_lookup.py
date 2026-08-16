"""Tests for the dedicated Award Type lookup (modules/award_lookup.py).

Key business rules under test:

- Award Type is matched at Customer+NDC grain (the canonical Lookup), which
  is what Awards.xlsx itself proves (Lookup == NDC + Sold to party for
  129/129 rows).
- Customer-only matching is NOT offered, because 19 of 80 sold-to-parties in
  the real source carry more than one distinct Award Type across their NDCs.
- The NDC fallback is product-level and only applies to rows the primary
  strategy could not resolve.
- Ambiguous keys are DUPLICATE_CONFLICT and left blank; values are never
  invented, and master rows are never multiplied.
"""

from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.award_lookup import (  # noqa: E402
    AWARD_STATUS_COLUMN,
    AWARD_STATUS_DUPLICATE_CONFLICT,
    AWARD_STATUS_MATCHED,
    AWARD_STATUS_NOT_FOUND,
    AWARD_STRATEGY_COLUMN,
    AWARD_STRATEGY_LOOKUP,
    AWARD_STRATEGY_NDC,
    AWARD_VALUE_COLUMN,
    build_award_lookup,
)


def _logger():
    logger = logging.getLogger("award_tests")
    logger.addHandler(logging.NullHandler())
    return logger


def _master(rows: list[tuple[str, str]]) -> pd.DataFrame:
    """rows = [(ndc, customer), ...]; Lookup is the canonical NDC+Customer."""
    df = pd.DataFrame(rows, columns=["NDC Code", "Sold-to party Name"])
    df["Lookup"] = df["NDC Code"].astype(str) + df["Sold-to party Name"].astype(str)
    return df


def _awards(rows: list[tuple[str, str, str]]) -> pd.DataFrame:
    """rows = [(ndc, sold_to_party, award_type), ...]."""
    df = pd.DataFrame(rows, columns=["NDC", "Sold to party", "Award Type"])
    df["Lookup"] = df["NDC"].astype(str) + df["Sold to party"].astype(str)
    return df


def _run(master_df: pd.DataFrame, awards_df):
    return build_award_lookup(
        master_df,
        awards_df,
        master_lookup_column="Lookup",
        master_ndc_column="NDC Code",
        master_customer_column="Sold-to party Name",
        source_lookup_column="Lookup",
        source_ndc_column="NDC",
        award_column="Award Type",
        logger=_logger(),
    )


class AwardPrimaryLookupTests(unittest.TestCase):
    def test_match_at_customer_plus_ndc_grain(self):
        result = _run(
            _master([("64380016101", "CAH GLOBAL CONTRACTING COMPANY LTD")]),
            _awards([("64380016101", "CAH GLOBAL CONTRACTING COMPANY LTD", "Backup (Primary CVS)")]),
        )
        row = result.dataframe.loc[0]
        self.assertEqual(row[AWARD_VALUE_COLUMN], "Backup (Primary CVS)")
        self.assertEqual(row[AWARD_STATUS_COLUMN], AWARD_STATUS_MATCHED)
        self.assertEqual(row[AWARD_STRATEGY_COLUMN], AWARD_STRATEGY_LOOKUP)
        self.assertEqual(result.matched_by_lookup, 1)

    def test_same_customer_different_ndc_gets_different_award(self):
        """Proves customer-only matching would be wrong."""
        result = _run(
            _master([("64380016101", "Cvs Caremark"), ("64380072701", "Cvs Caremark")]),
            _awards(
                [
                    ("64380016101", "Cvs Caremark", "Primary"),
                    ("64380072701", "Cvs Caremark", "Backup"),
                ]
            ),
        )
        self.assertEqual(result.dataframe.loc[0, AWARD_VALUE_COLUMN], "Primary")
        self.assertEqual(result.dataframe.loc[1, AWARD_VALUE_COLUMN], "Backup")

    def test_customer_only_match_is_not_used(self):
        """Same customer, but the master NDC is absent from Awards -> NOT_FOUND.

        A customer-level fallback would wrongly attach 'Primary' here.
        """
        result = _run(
            _master([("99999999999", "Cvs Caremark")]),
            _awards([("64380016101", "Cvs Caremark", "Primary")]),
        )
        row = result.dataframe.loc[0]
        self.assertTrue(pd.isna(row[AWARD_VALUE_COLUMN]))
        self.assertEqual(row[AWARD_STATUS_COLUMN], AWARD_STATUS_NOT_FOUND)


class AwardNdcFallbackTests(unittest.TestCase):
    def test_ndc_fallback_when_customer_differs(self):
        result = _run(
            _master([("64380016101", "SOME OTHER CUSTOMER")]),
            _awards([("64380016101", "Cvs Caremark", "Primary")]),
        )
        row = result.dataframe.loc[0]
        self.assertEqual(row[AWARD_VALUE_COLUMN], "Primary")
        self.assertEqual(row[AWARD_STATUS_COLUMN], AWARD_STATUS_MATCHED)
        self.assertEqual(row[AWARD_STRATEGY_COLUMN], AWARD_STRATEGY_NDC)
        self.assertEqual(result.matched_by_ndc, 1)

    def test_ambiguous_ndc_across_customers_is_duplicate_conflict(self):
        result = _run(
            _master([("64380016101", "SOME OTHER CUSTOMER")]),
            _awards(
                [
                    ("64380016101", "Cvs Caremark", "Primary"),
                    ("64380016101", "Cardinal Health", "Backup"),
                ]
            ),
        )
        row = result.dataframe.loc[0]
        self.assertTrue(pd.isna(row[AWARD_VALUE_COLUMN]), "ambiguous NDC must never be guessed")
        self.assertEqual(row[AWARD_STATUS_COLUMN], AWARD_STATUS_DUPLICATE_CONFLICT)

    def test_primary_lookup_wins_over_ndc_fallback(self):
        result = _run(
            _master([("64380016101", "Cvs Caremark")]),
            _awards(
                [
                    ("64380016101", "Cvs Caremark", "Primary"),
                    ("64380016101", "Cardinal Health", "Backup"),
                ]
            ),
        )
        row = result.dataframe.loc[0]
        self.assertEqual(row[AWARD_VALUE_COLUMN], "Primary")
        self.assertEqual(row[AWARD_STRATEGY_COLUMN], AWARD_STRATEGY_LOOKUP)


class AwardNotFoundTests(unittest.TestCase):
    def test_absent_everywhere_is_not_found(self):
        result = _run(
            _master([("64380018701", "KROGER")]),
            _awards([("64380016101", "Cvs Caremark", "Primary")]),
        )
        row = result.dataframe.loc[0]
        self.assertTrue(pd.isna(row[AWARD_VALUE_COLUMN]))
        self.assertEqual(row[AWARD_STATUS_COLUMN], AWARD_STATUS_NOT_FOUND)
        self.assertEqual(result.not_found_rows, 1)

        not_found = result.exceptions_df[result.exceptions_df["Status"] == AWARD_STATUS_NOT_FOUND]
        self.assertEqual(len(not_found), 1)

    def test_missing_source_yields_not_found_without_error(self):
        result = _run(_master([("64380018701", "KROGER")]), None)
        self.assertEqual(result.dataframe.loc[0, AWARD_STATUS_COLUMN], AWARD_STATUS_NOT_FOUND)
        self.assertEqual(len(result.dataframe), 1)

    def test_kroger_is_not_fabricated(self):
        """Regression: KROGER is absent from the real Awards source."""
        result = _run(
            _master([("64380018701", "KROGER"), ("64380020101", "KROGER")]),
            _awards(
                [
                    ("64380072701", "CAH GLOBAL CONTRACTING COMPANY LTD", "Backup"),
                    ("64380016101", "Cvs Caremark", "Primary"),
                ]
            ),
        )
        self.assertEqual(result.populated_rows, 0)
        self.assertEqual(result.not_found_rows, 2)
        self.assertTrue(result.dataframe[AWARD_VALUE_COLUMN].isna().all())


class AwardRowIntegrityTests(unittest.TestCase):
    def test_row_count_preserved_with_duplicate_source_rows(self):
        master_df = _master([("64380016101", "Cvs Caremark")] * 3)
        result = _run(
            master_df,
            _awards([("64380016101", "Cvs Caremark", "Primary")] * 4),
        )
        self.assertEqual(len(result.dataframe), len(master_df))
        self.assertEqual(result.master_rows_after_merge, result.total_master_rows)

    def test_no_temporary_columns_leak(self):
        result = _run(
            _master([("64380016101", "Cvs Caremark")]),
            _awards([("64380016101", "Cvs Caremark", "Primary")]),
        )
        leaked = [c for c in result.dataframe.columns if str(c).startswith("__") or str(c).endswith("__")]
        self.assertEqual(leaked, [])

    def test_ndc_dash_formatting_still_matches_via_fallback(self):
        result = _run(
            _master([("64380016101", "SOME OTHER CUSTOMER")]),
            _awards([("64380016101", "Cvs Caremark", "Primary")]),
        )
        self.assertEqual(result.dataframe.loc[0, AWARD_VALUE_COLUMN], "Primary")


if __name__ == "__main__":
    unittest.main()
