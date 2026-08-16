from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


from modules.loader import WorkbookData


@dataclass(frozen=True)
class JoinKeyCandidate:
    key_name: str
    normalized_hint: str
    workbook_count: int
    worksheet_count: int
    confidence_pct: float
    workbook_worksheet_locations: tuple[str, ...]


def _normalize_header(text: str) -> str:
    return " ".join(str(text).strip().lower().split())


def discover_join_key_candidates(
    loaded_workbooks: Dict[str, WorkbookData],
    join_key_hints: Dict[str, List[str] | tuple[str, ...]],
    logger,
) -> List[JoinKeyCandidate]:
    """Discover likely join keys across workbooks using configurable hint values."""
    total_worksheets = sum(len(workbook.worksheets) for workbook in loaded_workbooks.values())
    total_workbooks = len(loaded_workbooks)

    header_index: Dict[str, List[tuple[str, str, str]]] = {}
    for workbook in loaded_workbooks.values():
        for worksheet in workbook.worksheets.values():
            for column_name in worksheet.dataframe.columns:
                normalized = _normalize_header(str(column_name))
                header_index.setdefault(normalized, []).append((workbook.workbook_name, worksheet.sheet_name, str(column_name)))

    candidates: List[JoinKeyCandidate] = []
    for key_name, hints in join_key_hints.items():
        matched_locations: List[tuple[str, str, str]] = []
        for hint in hints:
            normalized_hint = _normalize_header(str(hint))
            matched_locations.extend(header_index.get(normalized_hint, []))

        if not matched_locations:
            continue

        unique_workbooks = sorted({item[0] for item in matched_locations})
        unique_worksheets = sorted({(item[0], item[1]) for item in matched_locations})

        workbook_coverage = len(unique_workbooks) / total_workbooks if total_workbooks else 0.0
        worksheet_coverage = len(unique_worksheets) / total_worksheets if total_worksheets else 0.0
        confidence_pct = round((workbook_coverage * 0.7 + worksheet_coverage * 0.3) * 100, 2)

        candidates.append(
            JoinKeyCandidate(
                key_name=key_name,
                normalized_hint=", ".join(str(h) for h in hints),
                workbook_count=len(unique_workbooks),
                worksheet_count=len(unique_worksheets),
                confidence_pct=confidence_pct,
                workbook_worksheet_locations=tuple(f"{wb}::{ws}" for wb, ws in unique_worksheets),
            )
        )

        logger.info(
            "Join key candidate=%s workbook_count=%s worksheet_count=%s confidence=%s",
            key_name,
            len(unique_workbooks),
            len(unique_worksheets),
            confidence_pct,
        )

    return sorted(candidates, key=lambda item: item.confidence_pct, reverse=True)


def build_join_key_analysis_markdown(candidates: List[JoinKeyCandidate]) -> str:
    """Build docs/JOIN_KEY_ANALYSIS.md content."""
    lines = [
        "# JOIN_KEY_ANALYSIS",
        "",
        "Generated from Phase 1 header discovery across loaded workbooks.",
        "",
        "| Candidate Key | Header Hints | Workbook Coverage | Worksheet Coverage | Confidence % | Locations |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    if not candidates:
        lines.append("| UNKNOWN | UNKNOWN | 0 | 0 | 0.0 | UNKNOWN |")
        return "\n".join(lines)

    for candidate in candidates:
        lines.append(
            "| {key} | {hints} | {workbooks} | {worksheets} | {confidence} | {locations} |".format(
                key=candidate.key_name,
                hints=candidate.normalized_hint.replace("|", "\\|"),
                workbooks=candidate.workbook_count,
                worksheets=candidate.worksheet_count,
                confidence=candidate.confidence_pct,
                locations=", ".join(candidate.workbook_worksheet_locations).replace("|", "\\|"),
            )
        )

    return "\n".join(lines)
