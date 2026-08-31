from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd

from modules.utils import normalize_text_key

# Month name variants observed in real Strend.xlsx headers (and reasonably
# expected future variants), mapped to their calendar month number. Matching
# is case-insensitive and tolerant of arbitrary surrounding whitespace.
_MONTH_NAME_TO_NUMBER: Dict[str, int] = {}
for _month_number in range(1, 13):
    _abbr = calendar.month_abbr[_month_number].lower()  # e.g. "jan"
    _full = calendar.month_name[_month_number].lower()  # e.g. "january"
    _MONTH_NAME_TO_NUMBER[_abbr] = _month_number
    _MONTH_NAME_TO_NUMBER[_full] = _month_number

# A few additional real-world spelling variants seen in the actual Strend
# workbook (e.g. "Sept" instead of "Sep", "June" already covered by _full).
_MONTH_NAME_TO_NUMBER.setdefault("sept", 9)

_HEADER_PATTERN = re.compile(
    r"^(?P<month>[A-Za-z]+)\.?\s*[\-\s]?\s*(?P<year>\d{2,4})$",
)


@dataclass(frozen=True)
class MonthColumnMatch:
    """A historical sales column matched to a specific calendar month/year."""

    header: str
    year: int
    month: int


@dataclass(frozen=True)
class HistoricalSalesResult:
    """Historical sales lookup result and supporting audit metrics."""

    dataframe: pd.DataFrame
    reporting_year: int
    reporting_month: int
    previous_month_labels: Tuple[str, ...]
    previous_month_headers: Tuple[Optional[str], ...]
    matched_lookup_count: int
    missing_lookup_count: int
    duplicate_lookup_keys: int


def _normalize_year(year_text: str) -> Optional[int]:
    if len(year_text) == 2:
        return 2000 + int(year_text)
    if len(year_text) == 4:
        return int(year_text)
    return None


def parse_month_column(header: str) -> Optional[MonthColumnMatch]:
    """Parse a Strend.xlsx column header into a (year, month) pair, if possible.

    Handles the real, inconsistent header formats observed in the workbook,
    e.g. " Jul-22 ", " Sept-23 ", " Dec 2024 ", " June-26 ". Returns ``None``
    for non-month columns (identifiers, forecast/average columns, etc.).
    """
    cleaned = header.strip()
    match = _HEADER_PATTERN.match(cleaned)
    if not match:
        return None

    month_text = match.group("month").strip().lower()
    year_text = match.group("year").strip()

    month_number = _MONTH_NAME_TO_NUMBER.get(month_text)
    if month_number is None:
        return None

    year_number = _normalize_year(year_text)
    if year_number is None:
        return None

    return MonthColumnMatch(header=header, year=year_number, month=month_number)


def discover_month_columns(columns: Sequence[str]) -> Dict[Tuple[int, int], str]:
    """Map every (year, month) found in ``columns`` to its original header text.

    If more than one column resolves to the same (year, month), the first
    encountered column wins and a warning should be logged by the caller.
    """
    mapping: Dict[Tuple[int, int], str] = {}
    for column in columns:
        parsed = parse_month_column(str(column))
        if parsed is None:
            continue
        key = (parsed.year, parsed.month)
        if key not in mapping:
            mapping[key] = parsed.header
    return mapping


def determine_reporting_period(master_df: pd.DataFrame, po_date_column: str, logger) -> Tuple[int, int]:
    """Determine the reporting year/month from the most common PO date month.

    Falls back to the current system date if ``po_date_column`` is missing
    or entirely empty, since no other explicit "reporting month" field
    exists in the source data.
    """
    if po_date_column in master_df.columns:
        raw_dates = master_df[po_date_column]
        if pd.api.types.is_numeric_dtype(raw_dates):
            # Excel stores dates as a day-count serial number (days since
            # 1899-12-30). When the source file leaves this column
            # unformatted, pandas reads it as a plain integer rather than a
            # datetime. Feeding that integer straight to pd.to_datetime()
            # would misinterpret it as nanoseconds since the Unix epoch,
            # producing bogus 1970-ish dates instead of the real date.
            parsed_dates = pd.to_datetime(raw_dates, unit="D", origin="1899-12-30", errors="coerce")
        else:
            parsed_dates = pd.to_datetime(raw_dates, errors="coerce")
        valid_dates = parsed_dates.dropna()
        if not valid_dates.empty:
            year_month_counts = valid_dates.dt.to_period("M").value_counts()
            most_common_period = year_month_counts.idxmax()
            logger.info(
                "Determined reporting period from '%s': %s-%02d",
                po_date_column,
                most_common_period.year,
                most_common_period.month,
            )
            return int(most_common_period.year), int(most_common_period.month)

    today = date.today()
    logger.warning(
        "Could not determine reporting period from '%s'; falling back to current system date %s-%02d",
        po_date_column,
        today.year,
        today.month,
    )
    return today.year, today.month


def previous_n_months(year: int, month: int, count: int = 3) -> List[Tuple[int, int]]:
    """Return the ``count`` calendar months preceding (year, month), oldest first.

    Handles year rollover correctly (e.g. reporting month January returns
    October/November/December of the previous year).
    """
    results: List[Tuple[int, int]] = []
    current_year, current_month = year, month
    for _ in range(count):
        current_month -= 1
        if current_month == 0:
            current_month = 12
            current_year -= 1
        results.append((current_year, current_month))
    results.reverse()
    return results


def month_label(month_number: int) -> str:
    """Return the short display label for a calendar month (e.g. 'Apr')."""
    return calendar.month_abbr[month_number]


# ---------------------------------------------------------------------------
# DYNAMIC STREND COLUMN RESOLUTION
# ---------------------------------------------------------------------------
# Strend.xlsx gains a new set of columns every month (" Jul-26 " becomes
# " Aug-26 ", " July'26- Forecast " becomes " Aug'26- Forecast ", and the
# rolling average window shifts). The helpers below locate those columns by
# PATTERN instead of by hardcoded header text, so a new monthly Strend export
# is picked up automatically with no code change.
#
# All matching is case-insensitive and tolerant of the arbitrary leading and
# trailing whitespace present in the real workbook headers. The ORIGINAL
# header text is always returned unchanged, so downstream selection/merging
# still uses the exact business header from the file.

# " July'26- Forecast ", " Jul-26 Forecast ", " Aug'26 forecast "
_FORECAST_PATTERN = re.compile(
    r"^(?P<month>[A-Za-z]+)\.?\s*['\-\s]?\s*(?P<year>\d{2,4})\s*[\-\s]*forecast$",
    re.IGNORECASE,
)

# " Avg Jan'26 to June'26 ", " Average Jan-26 to Jun-26 "
_ROLLING_AVERAGE_PATTERN = re.compile(
    r"^(?:avg|average)\b.*\bto\b.*$",
    re.IGNORECASE,
)


def find_month_header(columns: Sequence[str], year: int, month: int) -> Optional[str]:
    """Return the original header for a specific (year, month), if present."""
    return discover_month_columns(columns).get((year, month))


def find_latest_month_header(columns: Sequence[str]) -> Optional[str]:
    """Return the original header of the most recent month column present.

    Used when no explicit reporting period is available: the newest month in
    the Strend export is, by construction, the current reporting month.
    """
    month_map = discover_month_columns(columns)
    if not month_map:
        return None
    return month_map[max(month_map)]


def find_forecast_header(
    columns: Sequence[str],
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> Optional[str]:
    """Return the original header of the Forecast column.

    When ``year``/``month`` are supplied, only a forecast column for that exact
    period matches. Otherwise the forecast column for the LATEST period found
    is returned, so the newest monthly export is used automatically.
    """
    candidates: Dict[Tuple[int, int], str] = {}
    for column in columns:
        text = str(column).strip()
        match = _FORECAST_PATTERN.match(text)
        if not match:
            continue
        month_number = _MONTH_NAME_TO_NUMBER.get(match.group("month").strip().lower())
        year_number = _normalize_year(match.group("year").strip())
        if month_number is None or year_number is None:
            continue
        candidates.setdefault((year_number, month_number), str(column))

    if not candidates:
        return None
    if year is not None and month is not None:
        return candidates.get((year, month))
    return candidates[max(candidates)]


def find_rolling_average_header(columns: Sequence[str]) -> Optional[str]:
    """Return the original header of the rolling-average column, if present.

    Matches headers such as " Avg Jan'26 to June'26 " without depending on the
    specific months in the window, which shift with every monthly export.
    """
    for column in columns:
        if _ROLLING_AVERAGE_PATTERN.match(str(column).strip()):
            return str(column)
    return None


def resolve_sales_trend_payload_columns(
    columns: Sequence[str],
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> Tuple[str, ...]:
    """Resolve the period-specific Strend payload columns for the merge.

    Returns the ORIGINAL header text (in file order of significance) for the
    current month, its forecast, and the rolling-average column. Any column
    that is absent from this month's export is simply omitted, so the merge
    degrades gracefully instead of silently matching nothing.
    """
    resolved: List[str] = []

    month_header = (
        find_month_header(columns, year, month)
        if year is not None and month is not None
        else find_latest_month_header(columns)
    )
    forecast_header = find_forecast_header(columns, year, month)
    average_header = find_rolling_average_header(columns)

    for header in (month_header, forecast_header, average_header):
        if header is not None and header not in resolved:
            resolved.append(header)

    return tuple(resolved)


def build_historical_sales(
    strend_df: pd.DataFrame,
    master_lookup_keys: pd.Series,
    reporting_year: int,
    reporting_month: int,
    logger,
) -> HistoricalSalesResult:
    """Build a historical sales lookup table for the previous 3 months.

    Args:
        strend_df: Raw Strend.xlsx dataframe (exact original headers).
        master_lookup_keys: The ``Lookup`` column values from master_df,
            used only to report match/miss statistics (matching itself is
            performed by the caller via a standard dataframe merge).
        reporting_year/reporting_month: The reporting period as determined
            by ``determine_reporting_period``.
        logger: Standard pipeline logger.

    Returns:
        HistoricalSalesResult with a dataframe indexed by normalized Lookup
        key, containing one column per previous month (labelled with the
        actual month abbreviation, e.g. "Apr", "May", "Jun") plus "Average".
    """
    if "x" not in strend_df.columns and "Lookup" not in strend_df.columns:
        raise ValueError(
            "Strend dataframe is missing the historical sales key column. "
            "Expected either 'x' or 'Lookup' (exact business header)."
        )
    lookup_column = "Lookup" if "Lookup" in strend_df.columns else "x"

    month_column_map = discover_month_columns(list(strend_df.columns))
    previous_months = previous_n_months(reporting_year, reporting_month, count=3)

    previous_month_labels = tuple(month_label(month) for _, month in previous_months)
    previous_month_headers = tuple(month_column_map.get(key) for key in previous_months)

    for (year, month), header in zip(previous_months, previous_month_headers):
        if header is None:
            logger.warning(
                "No historical sales column found in Strend for %s-%02d; values will be left blank",
                year,
                month,
            )

    working = strend_df.copy()
    working["__lookup_key__"] = working[lookup_column].apply(normalize_text_key)

    duplicate_lookup_keys = int(working["__lookup_key__"].dropna().duplicated().sum())
    if duplicate_lookup_keys > 0:
        logger.warning("Duplicate historical Lookup keys detected in Strend: %s", duplicate_lookup_keys)

    result_columns: Dict[str, pd.Series] = {}
    for label, header in zip(previous_month_labels, previous_month_headers):
        if header is not None:
            result_columns[label] = pd.to_numeric(
                working[header].astype(str).str.replace(",", "", regex=False).str.strip(),
                errors="coerce",
            )
        else:
            result_columns[label] = pd.Series(pd.NA, index=working.index, dtype="Float64")

    historical_df = pd.DataFrame(result_columns, index=working.index)
    historical_df.insert(0, "__lookup_key__", working["__lookup_key__"])

    # Average across previous months. Missing values are excluded from the
    # average rather than silently treated as zero (explicit business rule
    # confirmation required before changing this behavior).
    month_value_columns = list(previous_month_labels)
    historical_df["Average"] = historical_df[month_value_columns].mean(axis=1, skipna=True)

    # Deduplicate on lookup key (first occurrence wins) for the merge step;
    # duplicates are already reported above for the Exceptions sheet.
    historical_df = historical_df.drop_duplicates(subset="__lookup_key__", keep="first")

    normalized_master_keys = master_lookup_keys.apply(normalize_text_key)
    matched_lookup_count = int(normalized_master_keys.isin(historical_df["__lookup_key__"].dropna()).sum())
    missing_lookup_count = int(len(normalized_master_keys) - matched_lookup_count)

    logger.info(
        "Historical sales stats | reporting_period=%s-%02d | matched=%s | missing=%s | duplicate_keys=%s",
        reporting_year,
        reporting_month,
        matched_lookup_count,
        missing_lookup_count,
        duplicate_lookup_keys,
    )

    return HistoricalSalesResult(
        dataframe=historical_df,
        reporting_year=reporting_year,
        reporting_month=reporting_month,
        previous_month_labels=previous_month_labels,
        previous_month_headers=previous_month_headers,
        matched_lookup_count=matched_lookup_count,
        missing_lookup_count=missing_lookup_count,
        duplicate_lookup_keys=duplicate_lookup_keys,
    )
