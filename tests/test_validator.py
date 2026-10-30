from decimal import Decimal
import pytest
from src.models import RawCustomerRecord, ValidatedCustomerRecord
from src.validator import validate_all, validate_record


def test_validate_record_success():
    """Test validating a fully compliant raw record."""
    raw = RawCustomerRecord(
        customer_name="John Doe",
        email="john.doe@example.com",
        tax_year="2023",
        income="$120,500.00",
        withholding="$25,000.50",
        source_file="doc.pdf",
    )
    validated, errors = validate_record(raw)

    assert errors == []
    assert isinstance(validated, ValidatedCustomerRecord)
    assert validated.customer_name == "John Doe"
    assert validated.email == "john.doe@example.com"
    assert validated.tax_year == 2023
    assert isinstance(validated.income, Decimal)
    assert isinstance(validated.withholding, Decimal)
    assert validated.income == Decimal("120500.00")
    assert validated.withholding == Decimal("25000.50")
    assert validated.source_file == "doc.pdf"


@pytest.mark.parametrize(
    "field_name",
    ["customer_name", "email", "tax_year", "income", "withholding"],
)
def test_validate_record_missing_required_fields(field_name: str):
    """Test that missing or blank required fields are caught."""
    base_data = {
        "customer_name": "Jane Smith",
        "email": "jane@example.com",
        "tax_year": "2023",
        "income": "50000",
        "withholding": "5000",
        "source_file": "sample.html",
    }
    base_data[field_name] = ""
    raw = RawCustomerRecord(**base_data)

    validated, errors = validate_record(raw)
    assert validated is None
    assert any(err.field == field_name and "Missing required field" in err.message for err in errors)


@pytest.mark.parametrize(
    "bad_email",
    [
        "plainaddress",
        "@missingusername.com",
        "username@.com",
        "username@domain",
        "user name@domain.com",
    ],
)
def test_validate_record_invalid_email_format(bad_email: str):
    """Test that malformed email addresses are flagged."""
    raw = RawCustomerRecord(
        customer_name="Test User",
        email=bad_email,
        tax_year="2023",
        income="75000",
        withholding="10000",
    )
    validated, errors = validate_record(raw)

    assert validated is None
    assert any(err.field == "email" and "Invalid email format" in err.message for err in errors)


def test_validate_record_negative_income():
    """Test that negative income is flagged."""
    raw = RawCustomerRecord(
        customer_name="Negative Earner",
        email="neg@example.com",
        tax_year="2023",
        income="-$15,000.00",
        withholding="0.00",
    )
    validated, errors = validate_record(raw)

    assert validated is None
    assert any(err.field == "income" and "Negative income value is not permitted" in err.message for err in errors)


def test_validate_record_negative_withholding():
    """Test that negative withholding is flagged."""
    raw = RawCustomerRecord(
        customer_name="Test User",
        email="user@example.com",
        tax_year="2023",
        income="$50,000.00",
        withholding="-500.00",
    )
    validated, errors = validate_record(raw)

    assert validated is None
    assert any(err.field == "withholding" and "Negative withholding value is not permitted" in err.message for err in errors)


@pytest.mark.parametrize("invalid_num", ["abc", "$$$,$$$", "N/A", "twelve-thousand", "NaN", "Infinity", "-Infinity"])
def test_validate_record_non_numeric_values(invalid_num: str):
    """Test non-numeric income or withholding values."""
    raw = RawCustomerRecord(
        customer_name="Test User",
        email="user@example.com",
        tax_year="2023",
        income=invalid_num,
        withholding="5000",
    )
    validated, errors = validate_record(raw)
    assert validated is None
    assert any(err.field == "income" and "valid numeric amount" in err.message for err in errors)


@pytest.mark.parametrize("bad_year", ["1850", "2200", "twenty-twenty", "23"])
def test_validate_record_inconsistent_tax_year(bad_year: str):
    """Test invalid or out-of-range tax years."""
    raw = RawCustomerRecord(
        customer_name="Test User",
        email="user@example.com",
        tax_year=bad_year,
        income="60000",
        withholding="8000",
    )
    validated, errors = validate_record(raw)
    assert validated is None
    assert any(err.field == "tax_year" for err in errors)


def test_validate_all_batch():
    """Test batch validation compiling report."""
    valid_raw = RawCustomerRecord("Alice", "alice@test.com", "2023", "50000", "5000")
    invalid_raw = RawCustomerRecord("Bob", "", "2023", "-1000", "0")

    report = validate_all([valid_raw, invalid_raw])
    assert len(report.valid_records) == 1
    assert len(report.errors) == 2
    assert report.valid_records[0].customer_name == "Alice"

