from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.extract import extract_data
from src.transform import transform_data


REQUIRED_COLUMNS: dict[str, set[str]] = {
    "dim_date": {"date_id", "full_date", "year", "month", "day", "month_name"},
    "dim_campaign": {"campaign_id", "campaign_name", "source", "medium"},
    "dim_customer": {"customer_id", "user_pseudo_id", "customer_segment", "city", "state"},
    "dim_device": {"device_id", "device_category"},
    "fact_marketing_performance": {
        "date_id",
        "campaign_id",
        "customer_id",
        "device_id",
        "sessions",
        "events",
        "conversions",
        "impressions",
        "clicks",
        "cost",
        "revenue",
    },
}

METRIC_COLUMNS = ["cost", "revenue", "clicks", "impressions", "conversions"]
KEY_COLUMNS = ["campaign_id", "date_id", "customer_id", "device_id"]


@dataclass(frozen=True)
class ValidationResult:
    name: str
    passed: bool
    details: str


def _validate_tables_not_empty(tables: dict[str, pd.DataFrame]) -> ValidationResult:
    missing_or_empty = [
        table_name
        for table_name in REQUIRED_COLUMNS
        if table_name not in tables or tables[table_name].empty
    ]
    if missing_or_empty:
        return ValidationResult(
            name="tables_not_empty",
            passed=False,
            details="Missing or empty tables: " + ", ".join(missing_or_empty),
        )
    return ValidationResult(
        name="tables_not_empty",
        passed=True,
        details="All required tables are present and non-empty.",
    )


def _validate_required_columns(tables: dict[str, pd.DataFrame]) -> ValidationResult:
    failures: list[str] = []
    for table_name, required in REQUIRED_COLUMNS.items():
        if table_name not in tables:
            failures.append(f"{table_name}: table not provided")
            continue
        missing_columns = sorted(required - set(tables[table_name].columns))
        if missing_columns:
            failures.append(f"{table_name}: missing {', '.join(missing_columns)}")

    if failures:
        return ValidationResult(
            name="required_columns",
            passed=False,
            details=" | ".join(failures),
        )
    return ValidationResult(
        name="required_columns",
        passed=True,
        details="All required columns are available.",
    )


def _validate_no_negative_metrics(fact: pd.DataFrame) -> ValidationResult:
    invalid_columns: list[str] = []
    for column in METRIC_COLUMNS:
        numeric = pd.to_numeric(fact[column], errors="coerce")
        if numeric.isna().any():
            invalid_columns.append(f"{column} has non-numeric values")
            continue
        if (numeric < 0).any():
            invalid_columns.append(f"{column} has negative values")

    if invalid_columns:
        return ValidationResult(
            name="non_negative_metrics",
            passed=False,
            details="; ".join(invalid_columns),
        )
    return ValidationResult(
        name="non_negative_metrics",
        passed=True,
        details="Metrics are numeric and non-negative.",
    )


def _validate_dates(dim_date: pd.DataFrame, fact: pd.DataFrame) -> ValidationResult:
    parsed_dates = pd.to_datetime(dim_date["full_date"], errors="coerce")
    if parsed_dates.isna().any():
        return ValidationResult(
            name="valid_dates",
            passed=False,
            details="dim_date.full_date contains invalid date values.",
        )

    expected_ids = parsed_dates.dt.strftime("%Y%m%d").astype(int)
    actual_ids = pd.to_numeric(dim_date["date_id"], errors="coerce")
    if actual_ids.isna().any() or not expected_ids.equals(actual_ids.astype(int)):
        return ValidationResult(
            name="valid_dates",
            passed=False,
            details="dim_date.date_id does not match full_date (YYYYMMDD).",
        )

    fact_date_ids = pd.to_numeric(fact["date_id"], errors="coerce")
    if fact_date_ids.isna().any():
        return ValidationResult(
            name="valid_dates",
            passed=False,
            details="fact_marketing_performance.date_id has invalid values.",
        )

    valid_ids = set(actual_ids.astype(int).tolist())
    if not set(fact_date_ids.astype(int).tolist()).issubset(valid_ids):
        return ValidationResult(
            name="valid_dates",
            passed=False,
            details="fact_marketing_performance.date_id has values not found in dim_date.",
        )

    return ValidationResult(
        name="valid_dates",
        passed=True,
        details="Date fields are valid and consistent.",
    )


def _validate_fact_keys_filled(fact: pd.DataFrame) -> ValidationResult:
    issues: list[str] = []

    for column in KEY_COLUMNS:
        if fact[column].isna().any():
            issues.append(f"{column} contains null values")
            continue

        if column == "date_id":
            numeric = pd.to_numeric(fact[column], errors="coerce")
            if numeric.isna().any() or (numeric <= 0).any():
                issues.append("date_id must be a positive integer")
        else:
            as_text = fact[column].astype(str).str.strip()
            if (as_text == "").any():
                issues.append(f"{column} contains blank values")

    if issues:
        return ValidationResult(
            name="fact_keys_filled",
            passed=False,
            details="; ".join(issues),
        )
    return ValidationResult(
        name="fact_keys_filled",
        passed=True,
        details="fact keys are properly filled.",
    )


def _validate_revenue_not_null(fact: pd.DataFrame) -> ValidationResult:
    revenue = pd.to_numeric(fact["revenue"], errors="coerce")
    if revenue.isna().any():
        return ValidationResult(
            name="revenue_not_null",
            passed=False,
            details="revenue contains null or non-numeric values after transformation.",
        )
    return ValidationResult(
        name="revenue_not_null",
        passed=True,
        details="revenue nulls were treated correctly.",
    )


def _validate_zero_cost_safety(fact: pd.DataFrame) -> ValidationResult:
    cost = pd.to_numeric(fact["cost"], errors="coerce")
    if cost.isna().any():
        return ValidationResult(
            name="zero_cost_safety",
            passed=False,
            details="cost contains null or non-numeric values.",
        )

    zero_cost_rows = fact[cost == 0]
    if zero_cost_rows.empty:
        return ValidationResult(
            name="zero_cost_safety",
            passed=True,
            details="No zero-cost rows found; check is still valid.",
        )

    fields_to_check = ["revenue", "clicks", "impressions", "conversions", "sessions", "events"]
    for column in fields_to_check:
        numeric = pd.to_numeric(zero_cost_rows[column], errors="coerce")
        if numeric.isna().any():
            return ValidationResult(
                name="zero_cost_safety",
                passed=False,
                details=f"{column} has invalid values for zero-cost rows.",
            )

    return ValidationResult(
        name="zero_cost_safety",
        passed=True,
        details="Zero-cost rows are valid and do not break metric consistency.",
    )


def _print_summary(results: list[ValidationResult]) -> None:
    print("[quality] Validation summary:")
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"- {result.name}: {status} | {result.details}")


def run_quality_checks(tables: dict[str, pd.DataFrame]) -> bool:
    """
    Execute critical data quality validations for transformed dimensional tables.
    Returns True when all checks pass; raises ValueError on critical failures.
    """
    if not isinstance(tables, dict):
        raise ValueError("run_quality_checks expects a dictionary of DataFrames.")

    results: list[ValidationResult] = []
    results.append(_validate_tables_not_empty(tables))
    results.append(_validate_required_columns(tables))

    # Stop early only when core table structure is invalid.
    if not all(result.passed for result in results):
        _print_summary(results)
        failure_details = "; ".join(result.details for result in results if not result.passed)
        raise ValueError(f"Critical data quality failure: {failure_details}")

    dim_date = tables["dim_date"]
    fact = tables["fact_marketing_performance"]

    results.extend(
        [
            _validate_no_negative_metrics(fact),
            _validate_dates(dim_date, fact),
            _validate_fact_keys_filled(fact),
            _validate_revenue_not_null(fact),
            _validate_zero_cost_safety(fact),
        ]
    )

    _print_summary(results)

    failed = [result for result in results if not result.passed]
    if failed:
        failure_details = "; ".join(f"{result.name}: {result.details}" for result in failed)
        raise ValueError(f"Critical data quality failure: {failure_details}")

    return True


def main() -> None:
    extracted = extract_data()
    transformed = transform_data(extracted)
    run_quality_checks(transformed)
    print("[quality] All critical checks passed.")


if __name__ == "__main__":
    main()
