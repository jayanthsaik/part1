"""Tests for the dedicated NDC normalization used exclusively for join/matching.

Covers:
- LOOKUP_COLUMNS["ndc_code"] configuration correctness (must match the
  actual master workbook header "NDC Code", not a mistyped variant).
- Dashed vs undashed NDC values normalizing to the same key.
- Numeric NDC values stored as Excel floats (e.g. 64380201.0).
- Leading zeros are preserved.
- Blank / missing NDC values return None.
- Matching normalized NDC values without mutating the original column.
"""
import unittest

import pandas as pd

from config import LOOKUP_COLUMNS
from modules.utils import normalize_ndc_key


class TestNdcConfigurationCorrectness(unittest.TestCase):
    def test_lookup_columns_ndc_code_matches_master_header(self) -> None:
        """The configured NDC column name must exactly match the master
        orderbook's actual header ("NDC Code"), not a mistyped variant such
        as "NDC code". This is what previously caused Lookup to be entirely
        null on the master dataframe."""
        self.assertEqual(LOOKUP_COLUMNS["ndc_code"], "NDC Code")


class TestNormalizeNdcKey(unittest.TestCase):
    def test_dashed_and_undashed_ndc_normalize_to_same_key(self) -> None:
        dashed = "64380-201-01"
        undashed = "6438020101"
        self.assertEqual(normalize_ndc_key(dashed), normalize_ndc_key(undashed))
        self.assertEqual(normalize_ndc_key(dashed), "6438020101")

    def test_numeric_ndc_stored_as_excel_float(self) -> None:
        # Excel commonly stores numeric-looking NDC values as floats.
        self.assertEqual(normalize_ndc_key(64380201.0), "64380201")
        self.assertEqual(normalize_ndc_key(6438020101.0), "6438020101")

    def test_string_ndc_with_trailing_float_artifact(self) -> None:
        # Sometimes upstream coercion leaves a string like "64380201.0".
        self.assertEqual(normalize_ndc_key("64380201.0"), "64380201")

    def test_leading_zeros_preserved(self) -> None:
        self.assertEqual(normalize_ndc_key("00456"), "00456")
        self.assertEqual(normalize_ndc_key("0045-6"), "00456")

    def test_blank_and_missing_ndc_returns_none(self) -> None:
        self.assertIsNone(normalize_ndc_key(None))
        self.assertIsNone(normalize_ndc_key(""))
        self.assertIsNone(normalize_ndc_key("   "))
        self.assertIsNone(normalize_ndc_key(pd.NA))
        self.assertIsNone(normalize_ndc_key(float("nan")))

    def test_whitespace_and_separators_stripped(self) -> None:
        self.assertEqual(normalize_ndc_key("  64380 201 01  "), "6438020101")
        self.assertEqual(normalize_ndc_key("64380/201/01"), "6438020101")

    def test_matching_normalized_values_does_not_mutate_original_series(self) -> None:
        original = pd.Series(["64380-201-01", "64380-161-01"], name="NDC Code")
        normalized = original.apply(normalize_ndc_key)

        # Original series/column must remain untouched.
        self.assertEqual(original.tolist(), ["64380-201-01", "64380-161-01"])
        # Normalized keys strip dashes for matching purposes only.
        self.assertEqual(normalized.tolist(), ["6438020101", "6438016101"])

    def test_matching_source_and_master_when_digit_groups_align(self) -> None:
        # When the dashed segments in the source expand to the same digit
        # sequence as the master's plain numeric NDC, normalization allows
        # them to match without altering either original value.
        source_ndc = pd.Series(["64380-0201-01"])
        master_ndc = pd.Series(["64380020101"])
        normalized_source = source_ndc.apply(normalize_ndc_key)
        normalized_master = master_ndc.apply(normalize_ndc_key)
        self.assertEqual(normalized_source.tolist(), normalized_master.tolist())
        # Originals remain untouched.
        self.assertEqual(source_ndc.tolist(), ["64380-0201-01"])
        self.assertEqual(master_ndc.tolist(), ["64380020101"])


if __name__ == "__main__":
    unittest.main()
