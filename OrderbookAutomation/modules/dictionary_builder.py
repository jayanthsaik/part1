from __future__ import annotations

from typing import Dict, List

import pandas as pd

from modules.loader import WorkbookData


def _detect_business_meaning(column_name: str) -> str:
    name = str(column_name).lower()
    if "ndc" in name:
        return "Potential National Drug Code field"
    if "material" in name:
        return "Potential material identifier or description"
    if "customer" in name or "sold-to" in name or "sold to" in name:
        return "Potential customer/account field"
    if "qty" in name or "quantity" in name:
        return "Potential quantity field"
    if "date" in name:
        return "Potential date field"
    if "lookup" in name:
        return "Potential composite lookup key"
    return "UNKNOWN"


def _potential_join_key(column_name: str, join_key_hints: Dict[str, tuple[str, ...] | List[str]]) -> str:
    lower = str(column_name).lower()
    for key_name, hint_values in join_key_hints.items():
        for hint in hint_values:
            if str(hint).lower() == lower:
                return key_name
    return "UNKNOWN"


def _sample_value(series: pd.Series) -> str:
    for value in series.tolist():
        if pd.notna(value) and str(value).strip() != "":
            return str(value)
    return ""


def build_data_dictionary_markdown(loaded_workbooks: Dict[str, WorkbookData], join_key_hints: Dict[str, tuple[str, ...] | List[str]]) -> str:
    """Build docs/DATA_DICTIONARY.md content from loaded workbooks."""
    lines: List[str] = [
        "# DATA_DICTIONARY",
        "",
        "Generated from Phase 1 workbook ingestion.",
        "",
    ]

    workbook_order = sorted(loaded_workbooks.values(), key=lambda item: item.workbook_name.lower())
    for workbook_data in workbook_order:
        lines.extend([f"## {workbook_data.workbook_name}", ""])
        for worksheet_name in sorted(workbook_data.worksheets.keys()):
            worksheet_data = workbook_data.worksheets[worksheet_name]
            df = worksheet_data.dataframe

            lines.extend(
                [
                    f"### {worksheet_data.sheet_name}",
                    "",
                    "| Workbook | Worksheet | Exact Column Name | Detected Data Type | Sample Value | Null Count | Unique Count | Potential Join Key | Potential Business Meaning |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                ]
            )

            for column_name in df.columns:
                series = df[column_name]
                lines.append(
                    "| {workbook} | {worksheet} | {column} | {dtype} | {sample} | {null_count} | {unique_count} | {join_key} | {meaning} |".format(
                        workbook=workbook_data.workbook_name,
                        worksheet=worksheet_data.sheet_name,
                        column=str(column_name).replace("|", "\\|"),
                        dtype=str(series.dtype),
                        sample=_sample_value(series).replace("|", "\\|"),
                        null_count=int(series.isna().sum()),
                        unique_count=int(series.nunique(dropna=True)),
                        join_key=_potential_join_key(column_name, join_key_hints),
                        meaning=_detect_business_meaning(column_name),
                    )
                )
            lines.append("")

    return "\n".join(lines)
