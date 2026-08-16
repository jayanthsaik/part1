"""Tests for the multi-source Buying Group enrichment.

Covers, per the approved specification:

- matches sourced from each priority tier individually,
- identical values across all tiers (no conflict, no row multiplication),
- cross-source disagreement resolved deterministically by priority
  (higher-priority source wins; NOT a DUPLICATE_CONFLICT),
- same-priority conflicting values -> DUPLICATE_CONFLICT with a blank value,
- case / whitespace / hidden-character normalization,
- absence from every source -> NOT_FOUND (only after all sources checked),
- exact master row-count preservation,
- no temporary/internal key columns leaking onto the output dataframe,
- the KROGER regression scenario (absent from Buying_groups.xlsx and
  Open_Order_Summary.xlsx, present in Strend.xlsx as "Econdisc").
"""

from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import BUYING_GROUP_SOURCES  # noqa: E402
from modules.buying_group_lookup import (  # noqa: E402
    BUYING_GROUP_OUTPUT_COLUMN,
    BUYING_GROUP_SOURCE_COLUMN,
    BUYING_GROUP_STATUS_COLUMN,
    BUYING_GROUP_STATUS_DUPLICATE_CONFLICT,
    BUYING_GROUP_STATUS_LOWER_PRIORITY_DISAGREEMENT,
    BUYING_GROUP_STATUS_MATCHED,
    BUYING_GROUP_STATUS_NOT_FOUND,
    BUYING_GROUP_VALUE_COLUMN,
    build_buying_group_lookup,
)

MASTER_CUSTOMER_COLUMN = "Sold-to party Name"

BUYING_GROUPS_KEY = "buying_groups"
STREND_KEY = "sales_trend"
OPEN_ORDERS_KEY = "open_orders"


def _logger():
    logger = logging.getLogger("buying_group_tests")
    logger.addHandler(logging.NullHandler())
    return logger


def _master(customers: list[str]) -> pd.DataFrame:
    return pd.DataFrame({MASTER_CUSTOMER_COLUMN: customers, "NDC Code": ["64380018701"] * len(customers)})


def _buying_groups(rows: list[tuple[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["Customer", "Customer buying group"])


def _strend(rows: list[tuple[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["Sold-to party Name", "Cust Group"])


def _open_orders(rows: list[tuple[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["PH_SOLDTO_NAME", "Customer Group"])


def _run(master_df: pd.DataFrame, source_frames: dict):
    return build_buying_group_lookup(
        master_df,
        source_frames,
        master_customer_column=MASTER_CUSTOMER_COLUMN,
        buying_group_sources=BUYING_GROUP_SOURCES,
        logger=_logger(),
    )


class BuyingGroupSourcePriorityTests(unittest.TestCase):
    def test_source_priority_configuration_is_as_approved(self):
        """Priority order must be Buying_groups -> Strend -> Open_Order_Summary."""
        ordered = sorted(BUYING_GROUP_SOURCES, key=lambda source: source.priority)
        self.assertEqual(
            [(source.display_name, source.priority) for source in ordered],
            [("Buying_groups.xlsx", 1), ("Strend.xlsx", 2), ("Open_Order_Summary.xlsx", 3)],
        )


class BuyingGroupSingleSourceMatchTests(unittest.TestCase):
    def test_match_in_buying_groups_only(self):
        result = _run(
            _master(["Genetco Inc"]),
            {BUYING_GROUPS_KEY: _buying_groups([("Genetco Inc", "Premier Group")])},
        )
        row = result.dataframe.loc[0]
        self.assertEqual(row[BUYING_GROUP_VALUE_COLUMN], "Premier Group")
        self.assertEqual(row[BUYING_GROUP_SOURCE_COLUMN], "Buying_groups.xlsx")
        self.assertEqual(row[BUYING_GROUP_STATUS_COLUMN], BUYING_GROUP_STATUS_MATCHED)

    def test_match_in_strend_only(self):
        """A fallback match from a lower-priority source is still MATCHED."""
        result = _run(
            _master(["Kroger"]),
            {
                BUYING_GROUPS_KEY: _buying_groups([("Genetco Inc", "Premier Group")]),
                STREND_KEY: _strend([("Kroger", "Econdisc")]),
            },
        )
        row = result.dataframe.loc[0]
        self.assertEqual(row[BUYING_GROUP_VALUE_COLUMN], "Econdisc")
        self.assertEqual(row[BUYING_GROUP_SOURCE_COLUMN], "Strend.xlsx")
        self.assertEqual(row[BUYING_GROUP_STATUS_COLUMN], BUYING_GROUP_STATUS_MATCHED)

    def test_match_in_open_order_summary_only(self):
        result = _run(
            _master(["Center Well Pharmacy"]),
            {
                BUYING_GROUPS_KEY: _buying_groups([("Genetco Inc", "Premier Group")]),
                STREND_KEY: _strend([("Kroger", "Econdisc")]),
                OPEN_ORDERS_KEY: _open_orders([("CENTER WELL PHARMACY", "Humana")]),
            },
        )
        row = result.dataframe.loc[0]
        self.assertEqual(row[BUYING_GROUP_VALUE_COLUMN], "Humana")
        self.assertEqual(row[BUYING_GROUP_SOURCE_COLUMN], "Open_Order_Summary.xlsx")
        self.assertEqual(row[BUYING_GROUP_STATUS_COLUMN], BUYING_GROUP_STATUS_MATCHED)


class BuyingGroupCrossSourceResolutionTests(unittest.TestCase):
    def test_all_three_sources_agree(self):
        result = _run(
            _master(["Genetco Inc"]),
            {
                BUYING_GROUPS_KEY: _buying_groups([("Genetco Inc", "Premier Group")]),
                STREND_KEY: _strend([("Genetco Inc", "Premier Group")]),
                OPEN_ORDERS_KEY: _open_orders([("Genetco Inc", "Premier Group")]),
            },
        )
        self.assertEqual(len(result.dataframe), 1, "agreeing sources must not multiply master rows")
        row = result.dataframe.loc[0]
        self.assertEqual(row[BUYING_GROUP_VALUE_COLUMN], "Premier Group")
        self.assertEqual(row[BUYING_GROUP_SOURCE_COLUMN], "Buying_groups.xlsx")
        self.assertEqual(row[BUYING_GROUP_STATUS_COLUMN], BUYING_GROUP_STATUS_MATCHED)
        self.assertEqual(result.lower_priority_disagreements, 0)

    def test_higher_priority_source_wins_cross_source_disagreement(self):
        """Priority 1 wins; this is a resolution, NOT a DUPLICATE_CONFLICT."""
        result = _run(
            _master(["Customer X"]),
            {
                BUYING_GROUPS_KEY: _buying_groups([("Customer X", "Group A")]),
                STREND_KEY: _strend([("Customer X", "Group B")]),
                OPEN_ORDERS_KEY: _open_orders([("Customer X", "Group C")]),
            },
        )
        row = result.dataframe.loc[0]
        self.assertEqual(row[BUYING_GROUP_VALUE_COLUMN], "Group A")
        self.assertEqual(row[BUYING_GROUP_SOURCE_COLUMN], "Buying_groups.xlsx")
        self.assertEqual(row[BUYING_GROUP_STATUS_COLUMN], BUYING_GROUP_STATUS_MATCHED)
        self.assertEqual(result.conflicting_customers, 0, "cross-source difference is not a conflict")
        self.assertEqual(result.lower_priority_disagreements, 2)

        rejected = result.exceptions_df[
            result.exceptions_df["Status"] == BUYING_GROUP_STATUS_LOWER_PRIORITY_DISAGREEMENT
        ]
        self.assertEqual(sorted(rejected["Rejected Buying Group"]), ["Group B", "Group C"])
        self.assertEqual(sorted(rejected["Rejected Source"]), ["Open_Order_Summary.xlsx", "Strend.xlsx"])

    def test_strend_wins_over_open_orders_when_primary_absent(self):
        result = _run(
            _master(["Customer X"]),
            {
                STREND_KEY: _strend([("Customer X", "Group B")]),
                OPEN_ORDERS_KEY: _open_orders([("Customer X", "Group C")]),
            },
        )
        row = result.dataframe.loc[0]
        self.assertEqual(row[BUYING_GROUP_VALUE_COLUMN], "Group B")
        self.assertEqual(row[BUYING_GROUP_SOURCE_COLUMN], "Strend.xlsx")


class BuyingGroupConflictTests(unittest.TestCase):
    def test_same_priority_conflicting_values_is_duplicate_conflict(self):
        """Same tier, two distinct values, no deterministic rule -> blank."""
        result = _run(
            _master(["Genetco Inc"]),
            {BUYING_GROUPS_KEY: _buying_groups([("Genetco Inc", "Group A"), ("GENETCO INC", "Group B")])},
        )
        row = result.dataframe.loc[0]
        self.assertTrue(pd.isna(row[BUYING_GROUP_VALUE_COLUMN]), "conflicting value must never be guessed")
        self.assertEqual(row[BUYING_GROUP_STATUS_COLUMN], BUYING_GROUP_STATUS_DUPLICATE_CONFLICT)
        self.assertEqual(result.conflicting_customers, 1)

        conflicts = result.exceptions_df[result.exceptions_df["Status"] == BUYING_GROUP_STATUS_DUPLICATE_CONFLICT]
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts.iloc[0]["Rejected Source"], "Buying_groups.xlsx")

    def test_same_priority_conflict_does_not_fall_through_to_lower_priority(self):
        """A conflicted higher-priority customer stays DUPLICATE_CONFLICT."""
        result = _run(
            _master(["Genetco Inc"]),
            {
                BUYING_GROUPS_KEY: _buying_groups([("Genetco Inc", "Group A"), ("Genetco Inc", "Group B")]),
                STREND_KEY: _strend([("Genetco Inc", "Group C")]),
            },
        )
        row = result.dataframe.loc[0]
        self.assertEqual(row[BUYING_GROUP_STATUS_COLUMN], BUYING_GROUP_STATUS_DUPLICATE_CONFLICT)
        self.assertTrue(pd.isna(row[BUYING_GROUP_VALUE_COLUMN]))


class BuyingGroupNormalizationTests(unittest.TestCase):
    def test_case_differences_match(self):
        result = _run(
            _master(["genetco inc"]),
            {BUYING_GROUPS_KEY: _buying_groups([("GENETCO INC", "Premier Group")])},
        )
        self.assertEqual(result.dataframe.loc[0, BUYING_GROUP_VALUE_COLUMN], "Premier Group")

    def test_whitespace_differences_match(self):
        result = _run(
            _master(["  Genetco    Inc  "]),
            {BUYING_GROUPS_KEY: _buying_groups([("Genetco Inc", "Premier Group")])},
        )
        self.assertEqual(result.dataframe.loc[0, BUYING_GROUP_VALUE_COLUMN], "Premier Group")

    def test_hidden_characters_match(self):
        result = _run(
            _master(["Genetco\tInc\n"]),
            {BUYING_GROUPS_KEY: _buying_groups([("Genetco Inc", "Premier Group")])},
        )
        self.assertEqual(result.dataframe.loc[0, BUYING_GROUP_VALUE_COLUMN], "Premier Group")

    def test_exact_duplicates_across_sources_do_not_multiply_rows(self):
        result = _run(
            _master(["Genetco Inc", "Genetco Inc"]),
            {
                BUYING_GROUPS_KEY: _buying_groups([("Genetco Inc", "Premier Group")] * 5),
                STREND_KEY: _strend([("GENETCO  INC", "premier group")] * 4),
            },
        )
        self.assertEqual(len(result.dataframe), 2)
        self.assertEqual(result.master_rows_after_merge, result.total_master_rows)
        self.assertEqual(result.conflicting_customers, 0)


class BuyingGroupNotFoundTests(unittest.TestCase):
    def test_absent_from_all_sources_is_not_found(self):
        result = _run(
            _master(["Unknown Customer"]),
            {
                BUYING_GROUPS_KEY: _buying_groups([("Genetco Inc", "Premier Group")]),
                STREND_KEY: _strend([("Kroger", "Econdisc")]),
                OPEN_ORDERS_KEY: _open_orders([("CENTER WELL PHARMACY", "Humana")]),
            },
        )
        row = result.dataframe.loc[0]
        self.assertTrue(pd.isna(row[BUYING_GROUP_VALUE_COLUMN]), "values must never be fabricated")
        self.assertEqual(row[BUYING_GROUP_STATUS_COLUMN], BUYING_GROUP_STATUS_NOT_FOUND)
        self.assertTrue(pd.isna(row[BUYING_GROUP_SOURCE_COLUMN]))

        not_found = result.exceptions_df[result.exceptions_df["Status"] == BUYING_GROUP_STATUS_NOT_FOUND]
        self.assertEqual(len(not_found), 1)
        self.assertIn("ANY configured", not_found.iloc[0]["Reason"])

    def test_no_sources_available_yields_not_found_without_error(self):
        result = _run(_master(["Genetco Inc"]), {})
        self.assertEqual(result.dataframe.loc[0, BUYING_GROUP_STATUS_COLUMN], BUYING_GROUP_STATUS_NOT_FOUND)
        self.assertEqual(len(result.dataframe), 1)


class BuyingGroupOutputHygieneTests(unittest.TestCase):
    def test_no_temporary_columns_leak_onto_output(self):
        result = _run(
            _master(["Genetco Inc"]),
            {
                BUYING_GROUPS_KEY: _buying_groups([("Genetco Inc", "Premier Group")]),
                STREND_KEY: _strend([("Genetco Inc", "Premier Group")]),
            },
        )
        leaked = [
            column
            for column in result.dataframe.columns
            if column.startswith("__") or column.endswith("__") or column.endswith("__buying_group_source")
        ]
        self.assertEqual(leaked, [], f"temporary columns leaked into output: {leaked}")

    def test_business_facing_alias_column_is_published(self):
        """Phase 4 / POB Summary consumes "Buying Group"; it must be present."""
        result = _run(
            _master(["Genetco Inc"]),
            {BUYING_GROUPS_KEY: _buying_groups([("Genetco Inc", "Premier Group")])},
        )
        self.assertIn(BUYING_GROUP_OUTPUT_COLUMN, result.dataframe.columns)
        self.assertEqual(result.dataframe.loc[0, BUYING_GROUP_OUTPUT_COLUMN], "Premier Group")

    def test_master_row_count_is_always_preserved(self):
        master_df = _master(["Genetco Inc", "Kroger", "Unknown Customer", "Genetco Inc"])
        result = _run(
            master_df,
            {
                BUYING_GROUPS_KEY: _buying_groups([("Genetco Inc", "Premier Group")] * 3),
                STREND_KEY: _strend([("Kroger", "Econdisc"), ("Kroger", "Econdisc")]),
            },
        )
        self.assertEqual(len(result.dataframe), len(master_df))
        self.assertEqual(result.master_rows_after_merge, result.total_master_rows)

    def test_audit_dataframe_reports_matches_by_source(self):
        result = _run(
            _master(["Genetco Inc", "Kroger"]),
            {
                BUYING_GROUPS_KEY: _buying_groups([("Genetco Inc", "Premier Group")]),
                STREND_KEY: _strend([("Kroger", "Econdisc")]),
            },
        )
        metrics = dict(zip(result.audit_df["Metric"], result.audit_df["Value"]))
        self.assertEqual(metrics["Master rows matched from Buying_groups.xlsx"], 1)
        self.assertEqual(metrics["Master rows matched from Strend.xlsx"], 1)
        self.assertEqual(metrics["Total master rows"], 2)
        self.assertEqual(metrics["NOT_FOUND rows"], 0)


class KrogerRegressionTests(unittest.TestCase):
    """Explicit regression for the reported blank Buying Group defect.

    KROGER is absent from Buying_groups.xlsx and Open_Order_Summary.xlsx but
    present in Strend.xlsx with Cust Group = "Econdisc", so it must resolve
    via the priority-2 fallback rather than remaining blank/NOT_FOUND.
    """

    def setUp(self):
        self.buying_groups_df = _buying_groups(
            [("American Health Packaging", "AHP"), ("Genetco Inc", "Premier Group")]
        )
        self.strend_df = _strend([("Kroger", "Econdisc"), ("Genetco Inc", "Premier Group")])
        self.open_orders_df = _open_orders([("CENTER WELL PHARMACY", "Humana")])

    def test_kroger_is_absent_from_primary_and_tertiary_sources(self):
        self.assertNotIn("KROGER", self.buying_groups_df["Customer"].str.upper().tolist())
        self.assertNotIn("KROGER", self.open_orders_df["PH_SOLDTO_NAME"].str.upper().tolist())

    def test_kroger_is_present_in_strend_as_econdisc(self):
        match = self.strend_df[self.strend_df["Sold-to party Name"].str.upper() == "KROGER"]
        self.assertEqual(len(match), 1)
        self.assertEqual(match.iloc[0]["Cust Group"], "Econdisc")

    def test_kroger_resolves_to_econdisc_from_strend(self):
        result = _run(
            _master(["KROGER"]),
            {
                BUYING_GROUPS_KEY: self.buying_groups_df,
                STREND_KEY: self.strend_df,
                OPEN_ORDERS_KEY: self.open_orders_df,
            },
        )
        row = result.dataframe.loc[0]
        self.assertEqual(row[BUYING_GROUP_VALUE_COLUMN], "Econdisc")
        self.assertEqual(row[BUYING_GROUP_OUTPUT_COLUMN], "Econdisc")
        self.assertEqual(row[BUYING_GROUP_SOURCE_COLUMN], "Strend.xlsx")
        self.assertEqual(row[BUYING_GROUP_STATUS_COLUMN], BUYING_GROUP_STATUS_MATCHED)
        self.assertEqual(len(result.dataframe), 1)


if __name__ == "__main__":
    unittest.main()
