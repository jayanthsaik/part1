"""Tests for the dedicated Buying Group lookup (modules/buying_group_lookup.py).

Covers:
- Case/whitespace/tab/newline normalization producing matches.
- Exact-duplicate source rows collapsing to a single lookup record without
  altering the master row count.
- Conflicting duplicate Customer -> different Buying Group mappings being
  flagged as DUPLICATE_CONFLICT (never guessed) and recorded as exceptions.
- Customers absent from the source remaining blank with NOT_FOUND status.
- The master row count is always preserved exactly.
- No temporary normalized columns leak into the returned dataframe.
"""
import logging
import unittest

import pandas as pd

from modules.buying_group_lookup import (
    BUYING_GROUP_STATUS_COLUMN,
    BUYING_GROUP_STATUS_DUPLICATE_CONFLICT,
    BUYING_GROUP_STATUS_MATCHED,
    BUYING_GROUP_STATUS_NOT_FOUND,
    build_buying_group_lookup,
)


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_buying_group_lookup")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


class TestBuyingGroupCaseAndWhitespaceMatching(unittest.TestCase):
    def test_case_difference_matches(self) -> None:
        master_df = pd.DataFrame({"Sold-to party Name": ["Genetco Inc"]})
        source_df = pd.DataFrame({"Customer": ["GENETCO INC"], "Customer buying group": ["Group A"]})
        result = build_buying_group_lookup(
            master_df,
            source_df,
            master_customer_column="Sold-to party Name",
            source_customer_column="Customer",
            source_buying_group_column="Customer buying group",
            logger=_silent_logger(),
        )
        self.assertEqual(result.dataframe.loc[0, "Customer buying group"], "Group A")
        self.assertEqual(result.dataframe.loc[0, BUYING_GROUP_STATUS_COLUMN], BUYING_GROUP_STATUS_MATCHED)

    def test_whitespace_tabs_and_repeated_spaces_match(self) -> None:
        master_df = pd.DataFrame({"Sold-to party Name": [" genetco   inc "]})
        source_df = pd.DataFrame({"Customer": ["Genetco\tInc"], "Customer buying group": ["Group A"]})
        result = build_buying_group_lookup(
            master_df,
            source_df,
            master_customer_column="Sold-to party Name",
            source_customer_column="Customer",
            source_buying_group_column="Customer buying group",
            logger=_silent_logger(),
        )
        self.assertEqual(result.dataframe.loc[0, "Customer buying group"], "Group A")
        self.assertEqual(result.dataframe.loc[0, BUYING_GROUP_STATUS_COLUMN], BUYING_GROUP_STATUS_MATCHED)

    def test_original_master_customer_column_not_mutated(self) -> None:
        master_df = pd.DataFrame({"Sold-to party Name": [" Genetco Inc "]})
        source_df = pd.DataFrame({"Customer": ["Genetco Inc"], "Customer buying group": ["Group A"]})
        result = build_buying_group_lookup(
            master_df,
            source_df,
            master_customer_column="Sold-to party Name",
            source_customer_column="Customer",
            source_buying_group_column="Customer buying group",
            logger=_silent_logger(),
        )
        self.assertEqual(result.dataframe.loc[0, "Sold-to party Name"], " Genetco Inc ")


class TestBuyingGroupExactDuplicates(unittest.TestCase):
    def test_exact_duplicate_source_rows_collapse_to_one_match(self) -> None:
        master_df = pd.DataFrame({"Sold-to party Name": ["Genetco Inc"]})
        source_df = pd.DataFrame(
            {
                "Customer": ["Genetco Inc", "Genetco Inc", "Genetco Inc"],
                "Customer buying group": ["Group A", "Group A", "Group A"],
            }
        )
        result = build_buying_group_lookup(
            master_df,
            source_df,
            master_customer_column="Sold-to party Name",
            source_customer_column="Customer",
            source_buying_group_column="Customer buying group",
            logger=_silent_logger(),
        )
        self.assertEqual(result.dataframe.loc[0, "Customer buying group"], "Group A")
        self.assertEqual(result.dataframe.loc[0, BUYING_GROUP_STATUS_COLUMN], BUYING_GROUP_STATUS_MATCHED)
        self.assertEqual(result.exact_duplicate_source_rows_removed, 2)
        # Master row count must not increase.
        self.assertEqual(result.master_rows_after_merge, 1)
        self.assertEqual(len(result.dataframe), 1)


class TestBuyingGroupConflictDetection(unittest.TestCase):
    def test_conflicting_buying_groups_are_flagged_not_guessed(self) -> None:
        master_df = pd.DataFrame({"Sold-to party Name": ["Genetco Inc"]})
        source_df = pd.DataFrame(
            {
                "Customer": ["Genetco Inc", "Genetco Inc"],
                "Customer buying group": ["Group A", "Group B"],
            }
        )
        result = build_buying_group_lookup(
            master_df,
            source_df,
            master_customer_column="Sold-to party Name",
            source_customer_column="Customer",
            source_buying_group_column="Customer buying group",
            logger=_silent_logger(),
        )
        self.assertTrue(pd.isna(result.dataframe.loc[0, "Customer buying group"]))
        self.assertEqual(result.dataframe.loc[0, BUYING_GROUP_STATUS_COLUMN], BUYING_GROUP_STATUS_DUPLICATE_CONFLICT)
        # Master row count must not increase.
        self.assertEqual(len(result.dataframe), 1)
        # Exception recorded.
        self.assertEqual(len(result.exceptions_df), 1)
        self.assertEqual(result.exceptions_df.iloc[0]["Status"], BUYING_GROUP_STATUS_DUPLICATE_CONFLICT)
        self.assertEqual(result.conflicting_customers, 1)


class TestBuyingGroupNotFound(unittest.TestCase):
    def test_customer_not_in_source_remains_blank_and_is_reported(self) -> None:
        master_df = pd.DataFrame({"Sold-to party Name": ["Unknown Customer"]})
        source_df = pd.DataFrame({"Customer": ["Genetco Inc"], "Customer buying group": ["Group A"]})
        result = build_buying_group_lookup(
            master_df,
            source_df,
            master_customer_column="Sold-to party Name",
            source_customer_column="Customer",
            source_buying_group_column="Customer buying group",
            logger=_silent_logger(),
        )
        self.assertTrue(pd.isna(result.dataframe.loc[0, "Customer buying group"]))
        self.assertEqual(result.dataframe.loc[0, BUYING_GROUP_STATUS_COLUMN], BUYING_GROUP_STATUS_NOT_FOUND)
        self.assertEqual(result.not_found_customers, 1)
        not_found_exceptions = result.exceptions_df[result.exceptions_df["Status"] == BUYING_GROUP_STATUS_NOT_FOUND]
        self.assertEqual(len(not_found_exceptions), 1)
        self.assertEqual(not_found_exceptions.iloc[0]["Customer"], "Unknown Customer")

    def test_does_not_invent_or_copy_value_from_another_customer(self) -> None:
        master_df = pd.DataFrame({"Sold-to party Name": ["Unknown Customer", "Genetco Inc"]})
        source_df = pd.DataFrame({"Customer": ["Genetco Inc"], "Customer buying group": ["Group A"]})
        result = build_buying_group_lookup(
            master_df,
            source_df,
            master_customer_column="Sold-to party Name",
            source_customer_column="Customer",
            source_buying_group_column="Customer buying group",
            logger=_silent_logger(),
        )
        self.assertTrue(pd.isna(result.dataframe.loc[0, "Customer buying group"]))
        self.assertEqual(result.dataframe.loc[1, "Customer buying group"], "Group A")


class TestBuyingGroupRowCountAndSchema(unittest.TestCase):
    def test_master_row_count_preserved_with_mixed_scenarios(self) -> None:
        master_df = pd.DataFrame(
            {
                "Sold-to party Name": [
                    "Genetco Inc",
                    "Genetco Inc",
                    "Conflict Co",
                    "Unknown Co",
                ]
            }
        )
        source_df = pd.DataFrame(
            {
                "Customer": ["Genetco Inc", "Genetco Inc", "Conflict Co", "Conflict Co"],
                "Customer buying group": ["Group A", "Group A", "Group X", "Group Y"],
            }
        )
        result = build_buying_group_lookup(
            master_df,
            source_df,
            master_customer_column="Sold-to party Name",
            source_customer_column="Customer",
            source_buying_group_column="Customer buying group",
            logger=_silent_logger(),
        )
        self.assertEqual(result.total_master_rows, 4)
        self.assertEqual(result.master_rows_after_merge, 4)
        self.assertEqual(len(result.dataframe), 4)

    def test_no_temporary_normalized_columns_leak_into_result(self) -> None:
        master_df = pd.DataFrame({"Sold-to party Name": ["Genetco Inc"]})
        source_df = pd.DataFrame({"Customer": ["Genetco Inc"], "Customer buying group": ["Group A"]})
        result = build_buying_group_lookup(
            master_df,
            source_df,
            master_customer_column="Sold-to party Name",
            source_customer_column="Customer",
            source_buying_group_column="Customer buying group",
            logger=_silent_logger(),
        )
        leaked_columns = [
            column
            for column in result.dataframe.columns
            if "Normalized" in column or column.startswith("__") or column in ("Lookup_x", "Lookup_y")
        ]
        self.assertEqual(leaked_columns, [])

    def test_missing_source_dataframe_leaves_blank_not_found(self) -> None:
        master_df = pd.DataFrame({"Sold-to party Name": ["Genetco Inc"]})
        result = build_buying_group_lookup(
            master_df,
            None,
            master_customer_column="Sold-to party Name",
            source_customer_column="Customer",
            source_buying_group_column="Customer buying group",
            logger=_silent_logger(),
        )
        self.assertTrue(pd.isna(result.dataframe.loc[0, "Customer buying group"]))
        self.assertEqual(result.dataframe.loc[0, BUYING_GROUP_STATUS_COLUMN], BUYING_GROUP_STATUS_NOT_FOUND)
        self.assertEqual(len(result.dataframe), 1)


if __name__ == "__main__":
    unittest.main()
