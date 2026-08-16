from __future__ import annotations

from typing import Sequence

import pandas as pd # pyright: ignore[reportMissingModuleSource]

from config import INVENTORY_COLUMNS, LOOKUP_COLUMNS, OPEN_ORDER_COLUMNS, ORDERBOOK_COLUMNS
from modules.utils import (
    clean_string_value,
    coerce_numeric_column,
    coerce_string_column,
    strip_trailing_zero,
)
from modules.validator import validate_dataframe_not_empty, validate_required_columns


def _clean_general_columns(
    df: pd.DataFrame,
    *,
    required_columns: Sequence[str],
    numeric_columns: Sequence[str],
    string_columns: Sequence[str],
) -> pd.DataFrame:
    working = df.copy()
    validate_dataframe_not_empty(working, "Input dataframe")
    validate_required_columns(working, required_columns, "Input dataframe")

    for column_name in required_columns:
        series = working[column_name]
        series = series.apply(clean_string_value)
        series = series.apply(strip_trailing_zero)
        if column_name in numeric_columns:
            working[column_name] = coerce_numeric_column(series)
        elif column_name in string_columns:
            working[column_name] = coerce_string_column(series)
        else:
            working[column_name] = series

    working = working.drop_duplicates(keep="first")
    return working


def clean_orderbook(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = tuple(ORDERBOOK_COLUMNS.values())
    numeric_columns = (
        ORDERBOOK_COLUMNS["sales_order_qty"],
        ORDERBOOK_COLUMNS["sales_qty_mtd"],
        ORDERBOOK_COLUMNS["forecast_qty"],
        ORDERBOOK_COLUMNS["sold_to_party"],
        ORDERBOOK_COLUMNS["ship_to_party"],
        ORDERBOOK_COLUMNS["unit_price"],
        ORDERBOOK_COLUMNS["sales_value_fc"],
        ORDERBOOK_COLUMNS["wac_bg_price_in_edi"],
        ORDERBOOK_COLUMNS["po_number"],
        ORDERBOOK_COLUMNS["postal_code"],
    )
    return _clean_general_columns(
        df,
        required_columns=required_columns,
        numeric_columns=numeric_columns,
        string_columns=(),
    )


def clean_lookup(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = (
        LOOKUP_COLUMNS["material_code"],
        LOOKUP_COLUMNS["ndc_code"],
        LOOKUP_COLUMNS["material_description"],
        LOOKUP_COLUMNS["pack_size_moq"],
    )
    return _clean_general_columns(
        df,
        required_columns=required_columns,
        numeric_columns=(LOOKUP_COLUMNS["pack_size_moq"],),
        string_columns=(),
    )


def clean_inventory(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = (
        INVENTORY_COLUMNS["ndc"],
        INVENTORY_COLUMNS["sku"],
        INVENTORY_COLUMNS["description"],
        INVENTORY_COLUMNS["actual_quantity"],
        INVENTORY_COLUMNS["allocated_quantity"],
        INVENTORY_COLUMNS["inventory"],
    )
    return _clean_general_columns(
        df,
        required_columns=required_columns,
        numeric_columns=(
            INVENTORY_COLUMNS["actual_quantity"],
            INVENTORY_COLUMNS["allocated_quantity"],
            INVENTORY_COLUMNS["inventory"],
        ),
        string_columns=(),
    )


def clean_open_orders(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = tuple(OPEN_ORDER_COLUMNS.values())
    return _clean_general_columns(
        df,
        required_columns=required_columns,
        numeric_columns=(
            OPEN_ORDER_COLUMNS["no_of_days"],
            OPEN_ORDER_COLUMNS["so_number"],
            OPEN_ORDER_COLUMNS["total"],
        ),
        string_columns=(),
    )
