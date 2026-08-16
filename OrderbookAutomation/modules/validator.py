from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from config import AppConfig
from modules.loader import WorkbookData


class DataValidationError(ValueError):
    """Raised when expected input data is missing or malformed."""


@dataclass(frozen=True)
class ValidationIssue:
    """Structured validation issue emitted during Phase 1 checks."""

    severity: str
    workbook: str
    worksheet: str
    issue_type: str
    details: str


@dataclass(frozen=True)
class ValidationResult:
    """Validation result bundle for ingestion pipeline."""

    issues: List[ValidationIssue]

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "ERROR" for issue in self.issues)


def validate_loaded_workbooks(config: AppConfig, loaded_workbooks: Dict[str, WorkbookData], logger) -> ValidationResult:
    """Validate workbook, worksheet, and header-level ingestion constraints."""
    issues: List[ValidationIssue] = []

    workbook_names = [workbook_data.workbook_name for workbook_data in loaded_workbooks.values()]
    if len(workbook_names) != len(set(workbook_names)):
        issues.append(
            ValidationIssue(
                severity="ERROR",
                workbook="",
                worksheet="",
                issue_type="DUPLICATE_WORKBOOK_NAME",
                details="Duplicate workbook names detected in loaded set",
            )
        )

    for workbook_key, spec in config.source_definitions.items():
        workbook_data = loaded_workbooks.get(workbook_key)
        if workbook_data is None:
            issues.append(
                ValidationIssue(
                    severity="ERROR" if spec.mandatory else "INFO",
                    workbook=spec.display_name,
                    worksheet="",
                    issue_type="MISSING_WORKBOOK" if spec.mandatory else "MISSING_OPTIONAL_WORKBOOK",
                    details=(
                        f"The '{spec.display_name}' source was not loaded. "
                        f"Hint: {spec.filename_hint or 'no additional hint available'}."
                    ),
                )
            )
            continue

        missing_sheets = [] if workbook_data.worksheets else ["<any>"]
        for sheet_name in missing_sheets:
            issues.append(
                ValidationIssue(
                    severity="ERROR",
                    workbook=spec.display_name,
                    worksheet=sheet_name,
                    issue_type="MISSING_WORKSHEET",
                    details="Workbook contains no readable worksheets",
                )
            )

        sheet_names = list(workbook_data.worksheets.keys())
        if len(sheet_names) != len(set(sheet_names)):
            issues.append(
                ValidationIssue(
                    severity="ERROR",
                    workbook=spec.display_name,
                    worksheet="",
                    issue_type="DUPLICATE_WORKSHEET_NAME",
                    details="Duplicate worksheet names detected",
                )
            )

        for worksheet_name, worksheet_data in workbook_data.worksheets.items():
            missing_required_headers = [
                header for header in spec.required_headers if header not in worksheet_data.dataframe.columns
            ]
            if missing_required_headers:
                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        workbook=spec.display_name,
                        worksheet=worksheet_name,
                        issue_type="MISSING_REQUIRED_COLUMN",
                        details=(
                            f"The '{spec.display_name}' workbook is missing required column(s): "
                            f"{missing_required_headers}"
                        ),
                    )
                )

            missing_optional_headers = [
                header for header in spec.optional_headers if header not in worksheet_data.dataframe.columns
            ]
            if missing_optional_headers:
                issues.append(
                    ValidationIssue(
                        severity="INFO",
                        workbook=spec.display_name,
                        worksheet=worksheet_name,
                        issue_type="MISSING_OPTIONAL_COLUMN",
                        details=f"Optional column(s) not present (non-blocking): {missing_optional_headers}",
                    )
                )
            dataframe = worksheet_data.dataframe

            if worksheet_data.duplicate_raw_headers:
                issues.append(
                    ValidationIssue(
                        severity="WARNING",
                        workbook=spec.display_name,
                        worksheet=worksheet_name,
                        issue_type="DUPLICATE_HEADERS",
                        details=f"Duplicate raw headers: {sorted(set(str(item) for item in worksheet_data.duplicate_raw_headers))}",
                    )
                )

            if worksheet_data.blank_raw_headers:
                issues.append(
                    ValidationIssue(
                        severity="WARNING",
                        workbook=spec.display_name,
                        worksheet=worksheet_name,
                        issue_type="BLANK_HEADERS",
                        details=f"Blank raw headers found: {len(worksheet_data.blank_raw_headers)}",
                    )
                )

            if worksheet_data.hidden_columns:
                issues.append(
                    ValidationIssue(
                        severity="WARNING",
                        workbook=spec.display_name,
                        worksheet=worksheet_name,
                        issue_type="HIDDEN_COLUMNS",
                        details=f"Hidden columns detected: {worksheet_data.hidden_columns}",
                    )
                )

            if worksheet_data.merged_header_ranges:
                issues.append(
                    ValidationIssue(
                        severity="WARNING",
                        workbook=spec.display_name,
                        worksheet=worksheet_name,
                        issue_type="MERGED_HEADERS",
                        details=f"Merged ranges detected: {worksheet_data.merged_header_ranges}",
                    )
                )

            empty_rows = int(dataframe.isna().all(axis=1).sum())
            if empty_rows > 0:
                issues.append(
                    ValidationIssue(
                        severity="INFO",
                        workbook=spec.display_name,
                        worksheet=worksheet_name,
                        issue_type="EMPTY_ROWS",
                        details=f"Completely blank rows: {empty_rows}",
                    )
                )

            empty_columns = [str(column) for column in dataframe.columns if dataframe[column].isna().all()]
            if empty_columns:
                issues.append(
                    ValidationIssue(
                        severity="WARNING",
                        workbook=spec.display_name,
                        worksheet=worksheet_name,
                        issue_type="EMPTY_COLUMNS",
                        details=f"Completely blank columns: {empty_columns}",
                    )
                )

    for issue in issues:
        if issue.severity == "ERROR":
            logger.error("%s | workbook=%s | worksheet=%s | %s", issue.issue_type, issue.workbook, issue.worksheet, issue.details)
        elif issue.severity == "WARNING":
            logger.warning("%s | workbook=%s | worksheet=%s | %s", issue.issue_type, issue.workbook, issue.worksheet, issue.details)
        else:
            logger.info("%s | workbook=%s | worksheet=%s | %s", issue.issue_type, issue.workbook, issue.worksheet, issue.details)

    return ValidationResult(issues=issues)
