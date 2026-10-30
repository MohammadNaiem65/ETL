from decimal import Decimal, InvalidOperation
import logging
from typing import List, Optional, Tuple

from src.constants import EMAIL_PATTERN, MAX_TAX_YEAR, MIN_TAX_YEAR
from src.models import (
    RawCustomerRecord,
    ValidatedCustomerRecord,
    ValidationError,
    ValidationReport,
)

logger = logging.getLogger(__name__)

# Parse a currency string to Decimal
def _parse_currency(value_str: str) -> Decimal:
    cleaned = value_str.strip().replace("$", "").replace(",", "")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    val = Decimal(cleaned)
    if not val.is_finite():
        raise InvalidOperation("Non-finite currency value")
    return val


def validate_record(
    record: RawCustomerRecord,
) -> Tuple[Optional[ValidatedCustomerRecord], List[ValidationError]]:
    errors: List[ValidationError] = []
    source = record.source_file

    # 1. Customer Name
    customer_name: Optional[str] = None
    if not record.customer_name or not record.customer_name.strip():
        errors.append(
            ValidationError(
                field="customer_name",
                message="Missing required field: customer_name",
                source_file=source,
            )
        )
    else:
        customer_name = record.customer_name.strip()

    # 2. Email
    email: Optional[str] = None
    if not record.email or not record.email.strip():
        errors.append(
            ValidationError(
                field="email",
                message="Missing required field: email",
                source_file=source,
            )
        )
    else:
        clean_email = record.email.strip()
        if not EMAIL_PATTERN.match(clean_email):
            errors.append(
                ValidationError(
                    field="email",
                    message=f"Invalid email format: '{clean_email}'",
                    source_file=source,
                )
            )
        else:
            email = clean_email

    # 3. Tax Year
    tax_year: Optional[int] = None
    if not record.tax_year or not str(record.tax_year).strip():
        errors.append(
            ValidationError(
                field="tax_year",
                message="Missing required field: tax_year",
                source_file=source,
            )
        )
    else:
        raw_year = str(record.tax_year).strip()
        try:
            year_int = int(raw_year)
            if year_int < MIN_TAX_YEAR or year_int > MAX_TAX_YEAR:
                errors.append(
                    ValidationError(
                        field="tax_year",
                        message=f"Inconsistent or out-of-range tax year: {year_int} (expected {MIN_TAX_YEAR}-{MAX_TAX_YEAR})",
                        source_file=source,
                    )
                )
            else:
                tax_year = year_int
        except ValueError:
            errors.append(
                ValidationError(
                    field="tax_year",
                    message=f"Tax year must be an integer, got '{raw_year}'",
                    source_file=source,
                )
            )

    # 4. Income
    income: Optional[Decimal] = None
    if not record.income or not str(record.income).strip():
        errors.append(
            ValidationError(
                field="income",
                message="Missing required field: income",
                source_file=source,
            )
        )
    else:
        raw_income = str(record.income).strip()
        try:
            parsed_income = _parse_currency(raw_income)
            if parsed_income < 0:
                errors.append(
                    ValidationError(
                        field="income",
                        message=f"Negative income value is not permitted: {parsed_income:.2f}",
                        source_file=source,
                    )
                )
            else:
                income = parsed_income
        except (InvalidOperation, ValueError):
            errors.append(
                ValidationError(
                    field="income",
                    message=f"Income must be a valid numeric amount, got '{raw_income}'",
                    source_file=source,
                )
            )

    # 5. Withholding
    withholding: Optional[Decimal] = None
    if not record.withholding or not str(record.withholding).strip():
        errors.append(
            ValidationError(
                field="withholding",
                message="Missing required field: withholding",
                source_file=source,
            )
        )
    else:
        raw_withholding = str(record.withholding).strip()
        try:
            parsed_withholding = _parse_currency(raw_withholding)
            if parsed_withholding < 0:
                errors.append(
                    ValidationError(
                        field="withholding",
                        message=f"Negative withholding value is not permitted: {parsed_withholding:.2f}",
                        source_file=source,
                    )
                )
            else:
                withholding = parsed_withholding
        except (InvalidOperation, ValueError):
            errors.append(
                ValidationError(
                    field="withholding",
                    message=f"Withholding must be a valid numeric amount, got '{raw_withholding}'",
                    source_file=source,
                )
            )

    if errors:
        return None, errors

    # All fields validated and non-None
    assert customer_name is not None
    assert email is not None
    assert tax_year is not None
    assert income is not None
    assert withholding is not None

    validated = ValidatedCustomerRecord(
        customer_name=customer_name,
        email=email,
        tax_year=tax_year,
        income=income,
        withholding=withholding,
        source_file=source,
    )
    return validated, []


def validate_all(records: List[RawCustomerRecord]) -> ValidationReport:
    valid_records: List[ValidatedCustomerRecord] = []
    all_errors: List[ValidationError] = []

    for record in records:
        valid_rec, errors = validate_record(record)
        if valid_rec is not None:
            valid_records.append(valid_rec)
        if errors:
            all_errors.extend(errors)

    return ValidationReport(valid_records=valid_records, errors=all_errors)

