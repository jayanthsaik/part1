"""Tests for the dedicated SC Comments lookup (modules/sc_comments_lookup.py).

Key business rules under test:

- NDC remains the primary (and only) key, per the documented VLOOKUP-on-NDC
  Critical Inventory Tracker process.
- Duplicate NDCs are NEVER silently resolved by keeping the first row. With
  no date/version column there is no valid "most recent tracker" rule, so
  conflicting comments are flagged DUPLICATE_CONFLICT and left blank.
- When a date/version column IS supplied, the most recent record wins.
- Comments are never invented and master rows are never multiplied.
"""

from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.sc_comments_lookup import (  # noqa: E402
    SC_COMMENTS_STATUS_COLUMN,
    SC_COMMENTS_STATUS_DUPLICATE_CONFLICT,
    SC_COMMENTS_STATUS_MATCHED,
    SC_COMMENTS_STATUS_NOT_FOUND,
    SC_COMMENTS_VALUE_COLUMN,
    build_sc_comments_lookup,
)


def _logger():
    logger = logging.getLogger("sc_comments_tests")
    logger.addHandler(logging.NullHandler())
    return logger


def _master(rows: list[tuple[object, str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["NDC Code", "Sold-to party Name"])


def _cip(rows: list[tuple[object, str]], dates: list | None = None) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=["NDC", "Comments"])
    if dates is not None:
        df["Tracker Date"] = dates
    return df


def _run(master_df, cip_df, date_column: str | None = None):
    return build_sc_comments_lookup(
        master_df,
        cip_df,
        master_ndc_column="NDC Code",
        master_customer_column="Sold-to party Name",
        source_ndc_column="NDC",
        source_comment_column="Comments",
        logger=_logger(),
        source_date_column=date_column,
    )


class ScCommentsMatchTests(unittest.TestCase):
    def test_match_by_ndc(self):
        result = _run(
            _master([(64380016101, "KROGER")]),
            _cip([(64380016101, "11K recd UPS")]),
        )
        row = result.dataframe.loc[0]
        self.assertEqual(row[SC_COMMENTS_VALUE_COLUMN], "11K recd UPS")
        self.assertEqual(row[SC_COMMENTS_STATUS_COLUMN], SC_COMMENTS_STATUS_MATCHED)

    def test_dashed_source_ndc_matches_plain_master_ndc(self):
        """Normalization is applied to temporary keys only."""
        result = _run(
            _master([("6438016101", "KROGER")]),
            _cip([("64380-161-01", "11K recd UPS")]),
        )
        self.assertEqual(result.dataframe.loc[0, SC_COMMENTS_VALUE_COLUMN], "11K recd UPS")

    def test_original_ndc_values_are_not_modified(self):
        master_df = _master([(64380016101, "KROGER")])
        original = master_df["NDC Code"].tolist()
        result = _run(master_df, _cip([(64380016101, "11K recd UPS")]))
        self.assertEqual(result.dataframe["NDC Code"].tolist(), original)


class ScCommentsDuplicateTests(unittest.TestCase):
    def test_exact_duplicate_comments_are_collapsed(self):
        result = _run(
            _master([(64380016101, "KROGER")]),
            _cip([(64380016101, "11K recd UPS"), (64380016101, "11K recd UPS")]),
        )
        row = result.dataframe.loc[0]
        self.assertEqual(row[SC_COMMENTS_VALUE_COLUMN], "11K recd UPS")
        self.assertEqual(row[SC_COMMENTS_STATUS_COLUMN], SC_COMMENTS_STATUS_MATCHED)
        self.assertEqual(result.exact_duplicate_source_rows_removed, 1)
        self.assertEqual(result.conflicting_ndcs, 0)

    def test_conflicting_comments_without_date_are_not_silently_resolved(self):
        result = _run(
            _master([(64380016101, "KROGER")]),
            _cip([(64380016101, "Comment A"), (64380016101, "Comment B")]),
        )
        row = result.dataframe.loc[0]
        self.assertTrue(pd.isna(row[SC_COMMENTS_VALUE_COLUMN]), "must not keep the first row silently")
        self.assertEqual(row[SC_COMMENTS_STATUS_COLUMN], SC_COMMENTS_STATUS_DUPLICATE_CONFLICT)
        self.assertEqual(result.conflicting_ndcs, 1)

        conflicts = result.exceptions_df[
            result.exceptions_df["Status"] == SC_COMMENTS_STATUS_DUPLICATE_CONFLICT
        ]
        self.assertEqual(len(conflicts), 1)
        self.assertIn("no date/version column", conflicts.iloc[0]["Reason"])

    def test_most_recent_record_wins_when_date_column_supplied(self):
        result = _run(
            _master([(64380016101, "KROGER")]),
            _cip(
                [(64380016101, "Older comment"), (64380016101, "Newer comment")],
                dates=["2026-07-01", "2026-08-15"],
            ),
            date_column="Tracker Date",
        )
        row = result.dataframe.loc[0]
        self.assertEqual(row[SC_COMMENTS_VALUE_COLUMN], "Newer comment")
        self.assertEqual(row[SC_COMMENTS_STATUS_COLUMN], SC_COMMENTS_STATUS_MATCHED)
        self.assertTrue(result.used_date_column)
        self.assertEqual(result.conflicting_ndcs, 0)


class ScCommentsNotFoundTests(unittest.TestCase):
    def test_ndc_absent_from_cip_is_not_found(self):
        result = _run(
            _master([(64380018701, "KROGER")]),
            _cip([(64380016101, "11K recd UPS")]),
        )
        row = result.dataframe.loc[0]
        self.assertTrue(pd.isna(row[SC_COMMENTS_VALUE_COLUMN]), "comments must never be invented")
        self.assertEqual(row[SC_COMMENTS_STATUS_COLUMN], SC_COMMENTS_STATUS_NOT_FOUND)

        not_found = result.exceptions_df[result.exceptions_df["Status"] == SC_COMMENTS_STATUS_NOT_FOUND]
        self.assertEqual(len(not_found), 1)

    def test_missing_source_yields_not_found_without_error(self):
        result = _run(_master([(64380018701, "KROGER")]), None)
        self.assertEqual(result.dataframe.loc[0, SC_COMMENTS_STATUS_COLUMN], SC_COMMENTS_STATUS_NOT_FOUND)
        self.assertEqual(len(result.dataframe), 1)

    def test_kroger_comments_are_not_fabricated(self):
        result = _run(
            _master([(64380018701, "KROGER"), (64380020101, "KROGER")]),
            _cip([(64380016001, "36K wk of 08/17"), (64380016601, "15K UPS Wk of 08/03")]),
        )
        self.assertEqual(result.populated_rows, 0)
        self.assertEqual(result.not_found_rows, 2)


class ScCommentsRowIntegrityTests(unittest.TestCase):
    def test_row_count_preserved(self):
        master_df = _master([(64380016101, "KROGER")] * 5)
        result = _run(master_df, _cip([(64380016101, "11K recd UPS")] * 3))
        self.assertEqual(len(result.dataframe), len(master_df))
        self.assertEqual(result.master_rows_after_merge, result.total_master_rows)

    def test_no_temporary_columns_leak(self):
        result = _run(
            _master([(64380016101, "KROGER")]),
            _cip([(64380016101, "11K recd UPS")]),
        )
        leaked = [c for c in result.dataframe.columns if str(c).startswith("__") or str(c).endswith("__")]
        self.assertEqual(leaked, [])


if __name__ == "__main__":
    unittest.main()
