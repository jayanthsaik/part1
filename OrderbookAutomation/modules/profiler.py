from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from modules.loader import WorkbookData


@dataclass(frozen=True)
class WorkbookSummaryRow:
    Workbook: str
    Worksheet: str
    Rows: int
    Columns: int
    Memory: int
    empty_rows: int
    empty_columns: int
    duplicate_rows: int


@dataclass(frozen=True)
class ColumnProfileRow:
    Workbook: str
    Worksheet: str
    Column_Name: str
    Data_Type: str
    Null_Count: int
    Unique_Count: int
    Sample_Value: str


def _sample_value(series: pd.Series) -> str:
    for value in series.tolist():
        if pd.notna(value) and str(value).strip() != "":
            return str(value)
    return ""


def build_workbook_profiles(loaded_workbooks: Dict[str, WorkbookData], logger) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build workbook summary and column-level profile dataframes."""
    summary_rows: List[WorkbookSummaryRow] = []
    column_rows: List[ColumnProfileRow] = []

    for workbook_data in loaded_workbooks.values():
        for worksheet_data in workbook_data.worksheets.values():
            df = worksheet_data.dataframe
            summary_rows.append(
                WorkbookSummaryRow(
                    Workbook=workbook_data.workbook_name,
                    Worksheet=worksheet_data.sheet_name,
                    Rows=int(len(df)),
                    Columns=int(len(df.columns)),
                    Memory=int(df.memory_usage(deep=True).sum()),
                    empty_rows=int(df.isna().all(axis=1).sum()),
                    empty_columns=int(sum(df[col].isna().all() for col in df.columns)),
                    duplicate_rows=int(df.duplicated().sum()),
                )
            )

            for column_name in df.columns:
                series = df[column_name]
                column_rows.append(
                    ColumnProfileRow(
                        Workbook=workbook_data.workbook_name,
                        Worksheet=worksheet_data.sheet_name,
                        Column_Name=str(column_name),
                        Data_Type=str(series.dtype),
                        Null_Count=int(series.isna().sum()),
                        Unique_Count=int(series.nunique(dropna=True)),
                        Sample_Value=_sample_value(series),
                    )
                )

            logger.info("Profiled workbook=%s sheet=%s", workbook_data.workbook_name, worksheet_data.sheet_name)

    summary_df = pd.DataFrame([row.__dict__ for row in summary_rows])
    columns_df = pd.DataFrame([row.__dict__ for row in column_rows])

    summary_df = summary_df.rename(
        columns={
            "empty_rows": "Empty Rows",
            "empty_columns": "Empty Columns",
            "duplicate_rows": "Duplicate Rows",
        }
    )
    columns_df = columns_df.rename(
        columns={
            "Column_Name": "Column Name",
            "Data_Type": "Data Type",
            "Null_Count": "Null Count",
            "Unique_Count": "Unique Count",
            "Sample_Value": "Sample Value",
        }
    )

    return summary_df, columns_df


def write_workbook_profile(summary_df: pd.DataFrame, columns_df: pd.DataFrame, output_path, logger) -> None:
    """Write workbook-level and column-level profile workbook."""
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Workbook Summary", index=False)
        columns_df.to_excel(writer, sheet_name="Columns", index=False)
    logger.info("Wrote Workbook_Profile.xlsx to %s", output_path)
