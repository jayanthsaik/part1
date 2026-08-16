from __future__ import annotations

import pandas as pd

from config import INVENTORY_COLUMNS, OPEN_ORDER_COLUMNS


def calculate_inventory_position(orderbook_df: pd.DataFrame, inventory_df: pd.DataFrame, open_orders_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    inventory_group_key = INVENTORY_COLUMNS["ndc"]
    inventory_value_column = INVENTORY_COLUMNS["actual_quantity"]
    open_orders_group_key = OPEN_ORDER_COLUMNS["sku"]
    open_orders_value_column = OPEN_ORDER_COLUMNS["total"]

    missing = [
        column
        for column in [inventory_group_key, inventory_value_column]
        if column not in inventory_df.columns
    ]
    if missing:
        raise ValueError(f"Inventory dataframe is missing required columns: {', '.join(missing)}")

    missing_open = [
        column
        for column in [open_orders_group_key, open_orders_value_column]
        if column not in open_orders_df.columns
    ]
    if missing_open:
        raise ValueError(f"Open orders dataframe is missing required columns: {', '.join(missing_open)}")

    inventory_summary = inventory_df.groupby(inventory_group_key, dropna=False)[inventory_value_column].sum().rename("inventory_qty").reset_index()
    open_order_summary = open_orders_df.groupby(open_orders_group_key, dropna=False)[open_orders_value_column].sum().rename("open_order_qty").reset_index()

    inventory_position = inventory_summary.copy()
    inventory_position["open_order_qty"] = 0
    inventory_position["net_inventory_qty"] = inventory_position["inventory_qty"]

    enriched_orderbook = orderbook_df.copy()
    enriched_orderbook["inventory_qty"] = pd.NA
    enriched_orderbook["open_order_qty"] = pd.NA
    enriched_orderbook["net_inventory_qty"] = pd.NA

    return enriched_orderbook, inventory_position
