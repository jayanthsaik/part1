import itertools

from modules.source_discovery import _normalize_header
from modules.source_registry import SOURCE_DEFINITIONS


def _normalized(headers):
    return {_normalize_header(h) for h in headers}


def test_no_source_signature_is_a_subset_of_another():
    """A source whose required headers are a subset of another source's full
    header set can be matched ambiguously during discovery."""
    for a, b in itertools.permutations(SOURCE_DEFINITIONS.values(), 2):
        a_required = _normalized(a.required_headers)
        b_all = _normalized(b.required_headers) | _normalized(b.optional_headers)
        assert not a_required.issubset(b_all), (
            f"'{a.logical_name}' required headers {sorted(a_required)} are a "
            f"subset of '{b.logical_name}' headers -- discovery is ambiguous."
        )


def test_upload_sheet_is_discriminated_by_reason_code():
    """Reason Code is the SOLE discriminator between upload_sheet and
    orderbook. If this ever fails, upload_sheet needs another required header."""
    upload = SOURCE_DEFINITIONS["upload_sheet"]
    orderbook = SOURCE_DEFINITIONS["orderbook"]
    orderbook_headers = _normalized(orderbook.required_headers) | _normalized(
        orderbook.optional_headers
    )
    discriminators = _normalized(upload.required_headers) - orderbook_headers
    assert _normalize_header("Reason Code") in discriminators


def test_header_normalization_variants_are_equivalent():
    canonical = _normalize_header("Reason Code")
    for variant in ("Reason code", "REASON CODE", "Reason_Code", "  Reason  Code ", "reason-code"):
        assert _normalize_header(variant) == canonical