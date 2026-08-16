import unittest

from modules.utils import normalize_identifier_key, normalize_text_key


class TestLookupNormalization(unittest.TestCase):
    def test_text_variants_normalize_to_same_key(self) -> None:
        variants = [
            "Bloodworth Wholesale",
            " bloodworth wholesale ",
            "BLOODWORTH WHOLESALE",
            "Bloodworth    Wholesale",
            "Bloodworth\tWholesale",
            "Bloodworth\nWholesale",
        ]
        normalized = {normalize_text_key(value) for value in variants}
        self.assertEqual(normalized, {"BLOODWORTH WHOLESALE"})

    def test_text_normalization_handles_nulls(self) -> None:
        self.assertIsNone(normalize_text_key(None))

    def test_identifier_normalization_does_not_force_uppercase(self) -> None:
        self.assertEqual(normalize_identifier_key("  abC123  "), "abC123")


if __name__ == "__main__":
    unittest.main()
