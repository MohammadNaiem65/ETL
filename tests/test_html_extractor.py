from pathlib import Path
import pytest
from src.html_extractor import extract_from_html
from src.models import RawCustomerRecord

# Test extracting from paragraph/strong tag format (sample_valid_1.html).
def test_extract_html_paragraph_format():
    file_path = "data/input/sample_valid_1.html"
    records = extract_from_html(file_path)

    assert len(records) == 1
    record = records[0]
    assert isinstance(record, RawCustomerRecord)
    assert record.customer_name == "Sarah Jenkins"
    assert record.email == "sarah.jenkins@workmail.io"
    assert record.tax_year == "2023"
    assert record.income == "$94,200.00"
    assert record.withholding == "$14,800.50"
    assert record.source_file == file_path

# Test extracting from two-column key-value table format (sample_valid_2.html).
def test_extract_html_table_format():
    file_path = "data/input/sample_valid_2.html"
    records = extract_from_html(file_path)

    assert len(records) == 1
    record = records[0]
    assert isinstance(record, RawCustomerRecord)
    assert record.customer_name == "David K. Miller"
    assert record.email == "david.miller@domain.com"
    assert record.tax_year == "2024"
    assert record.income == "$145,000"
    assert record.withholding == "$28,400"
    assert record.source_file == file_path

# Test extracting from a multi-column data table (customers_table.html).
def test_extract_html_multi_column_table():
    file_path = "data/input/customers_table.html"
    records = extract_from_html(file_path)

    assert len(records) == 3

    # Row 1: Avery Morgan
    assert records[0].customer_name == "Avery Morgan"
    assert records[0].email == "avery.morgan@example.test"
    assert records[0].tax_year == "2025"
    assert records[0].income == "78500.00"
    assert records[0].withholding == "9200.00"
    assert records[0].source_file == file_path

    # Row 2: Taylor Quinn (missing email)
    assert records[1].customer_name == "Taylor Quinn"
    assert records[1].email is None
    assert records[1].tax_year == "2025"
    assert records[1].income == "51000.00"
    assert records[1].withholding == "4300.00"

    # Row 3: Casey Rivera (negative income)
    assert records[2].customer_name == "Casey Rivera"
    assert records[2].email == "casey.rivera@example.test"
    assert records[2].tax_year == "2025"
    assert records[2].income == "-1250.00"
    assert records[2].withholding == "500.00"

# Test handling of a non-existent HTML file.
def test_extract_html_missing_file():
    fake_path = "data/input/non_existent_file.html"
    records = extract_from_html(fake_path)

    assert len(records) == 1
    record = records[0]
    assert isinstance(record, RawCustomerRecord)
    assert record.customer_name is None
    assert record.email is None
    assert record.source_file == fake_path

# Test parsing HTML with missing or unexpected structure.
def test_extract_html_unexpected_structure(tmp_path: Path):
    bad_html = tmp_path / "unexpected.html"
    bad_html.write_text("<html><body><div><h1>Just a title</h1></div></body></html>", encoding="utf-8")

    records = extract_from_html(bad_html)
    assert len(records) == 1
    record = records[0]
    assert record.customer_name is None
    assert record.email is None
    assert record.tax_year is None
    assert record.income is None
    assert record.withholding is None
    assert record.source_file == str(bad_html)

# Test parsing an empty HTML file.
def test_extract_html_empty_file(tmp_path: Path):
    empty_html = tmp_path / "empty.html"
    empty_html.write_text("", encoding="utf-8")

    records = extract_from_html(empty_html)
    assert len(records) == 1
    assert records[0].customer_name is None
    assert records[0].source_file == str(empty_html)

