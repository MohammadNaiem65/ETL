from pathlib import Path
import pytest
from src.pdf_extractor import extract_from_pdf
from src.models import RawCustomerRecord


def test_extract_pdf_colon_delimited():
    """Test extraction from standard colon-separated PDF (sample_valid_1.pdf)."""
    file_path = "data/input/sample_valid_1.pdf"
    records = extract_from_pdf(file_path)

    assert len(records) == 1
    record = records[0]
    assert isinstance(record, RawCustomerRecord)
    assert record.customer_name == "Alice Walker"
    assert record.email == "alice.walker@example.com"
    assert record.tax_year == "2023"
    assert record.income == "$85,000.00"
    assert record.withholding == "$12,500.00"
    assert record.source_file == file_path


def test_extract_pdf_table_layout():
    """Test extraction from table-formatted PDF (sample_valid_2.pdf)."""
    file_path = "data/input/sample_valid_2.pdf"
    records = extract_from_pdf(file_path)

    assert len(records) == 1
    record = records[0]
    assert isinstance(record, RawCustomerRecord)
    assert record.customer_name == "Robert Chen"
    assert record.email == "robert.chen@baytaxpro-client.org"
    assert record.tax_year == "2023"
    assert record.income == "112450.50"
    assert record.withholding == "21300.75"
    assert record.source_file == file_path


def test_extract_pdf_multi_column_table():
    """Test extraction from a multi-column data table (customers_2025_valid.pdf)."""
    file_path = "data/input/customers_2025_valid.pdf"
    records = extract_from_pdf(file_path)

    assert len(records) == 2

    # Row 1: Avery Morgan (email with newline unwrapped)
    assert records[0].customer_name == "Avery Morgan"
    assert records[0].email == "avery.morgan@example.test"
    assert records[0].tax_year == "2025"
    assert records[0].income == "78500.0"
    assert records[0].withholding == "9200.0"
    assert records[0].source_file == file_path

    # Row 2: Jordan Lee
    assert records[1].customer_name == "Jordan Lee"
    assert records[1].email == "jordan.lee@example.test"
    assert records[1].tax_year == "2025"
    assert records[1].income == "64200.0"
    assert records[1].withholding == "7100.0"
    assert records[1].source_file == file_path


def test_extract_pdf_with_negative_income_and_empty_email():
    """Test extraction from notice PDF with empty email label and negative income."""
    file_path = "data/input/sample_negative_income_missing_email.pdf"
    records = extract_from_pdf(file_path)

    assert len(records) == 1
    record = records[0]
    assert isinstance(record, RawCustomerRecord)
    assert record.customer_name == "Marcus Vance"
    assert record.email == ""
    assert record.tax_year == "2022"
    assert record.income == "-$15,200.00"
    assert record.withholding == "$0.00"
    assert record.source_file == file_path


def test_extract_pdf_corrupted_file():
    """Test extraction from a corrupted PDF (corrupted_tax_doc.pdf)."""
    file_path = "data/input/corrupted_tax_doc.pdf"
    records = extract_from_pdf(file_path)

    assert len(records) == 1
    record = records[0]
    assert isinstance(record, RawCustomerRecord)
    assert record.customer_name is None
    assert record.email is None
    assert record.tax_year is None
    assert record.income is None
    assert record.withholding is None
    assert record.source_file == file_path


def test_extract_pdf_missing_file():
    """Test extraction when the PDF file does not exist."""
    fake_path = "data/input/does_not_exist.pdf"
    records = extract_from_pdf(fake_path)

    assert len(records) == 1
    record = records[0]
    assert isinstance(record, RawCustomerRecord)
    assert record.customer_name is None
    assert record.source_file == fake_path

