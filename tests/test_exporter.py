import csv
import json
import pytest
import pdfplumber
from decimal import Decimal
from pathlib import Path

from src.constants import CSV_FIELDNAMES, RECORD_FIELDS
from src.exporter import (
    CSV_FIELDNAMES as EXPORTER_CSV_FIELDNAMES,
    export_to_csv,
    export_to_json,
    export_validation_report,
)
from src.models import ValidatedCustomerRecord, ValidationError, ValidationReport
from src.pdf_generator import generate_pdf_report


@pytest.fixture
def sample_records():
    return [
        ValidatedCustomerRecord(
            customer_name="Alice Smith",
            email="alice@example.com",
            tax_year=2023,
            income=Decimal("95000.0"),
            withholding=Decimal("15000.0"),
            source_file="alice.html",
        ),
        ValidatedCustomerRecord(
            customer_name="Bob Jones",
            email="bob@example.com",
            tax_year=2024,
            income=Decimal("80000.5"),
            withholding=Decimal("12000.25"),
            source_file="bob.pdf",
        ),
    ]


def test_export_to_csv(tmp_path: Path, sample_records):
    """Test exporting records to CSV with correct headers and rows."""
    assert EXPORTER_CSV_FIELDNAMES == CSV_FIELDNAMES
    assert CSV_FIELDNAMES == [*RECORD_FIELDS, "source_file"]

    csv_file = tmp_path / "test_records.csv"
    result_path = export_to_csv(sample_records, csv_file)

    assert result_path.exists()
    with result_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == CSV_FIELDNAMES
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["customer_name"] == "Alice Smith"
        assert Decimal(rows[0]["income"]) == Decimal("95000.0")
        assert rows[1]["customer_name"] == "Bob Jones"
        assert Decimal(rows[1]["withholding"]) == Decimal("12000.25")


def test_export_to_json(tmp_path: Path, sample_records):
    """Test exporting records to JSON format."""
    json_file = tmp_path / "test_records.json"
    result_path = export_to_json(sample_records, json_file)

    assert result_path.exists()
    with result_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == 2
        assert data[0]["customer_name"] == "Alice Smith"
        assert data[0]["tax_year"] == 2023
        assert data[0]["income"] == 95000.0
        assert data[1]["withholding"] == 12000.25


def test_export_validation_report(tmp_path: Path, sample_records):
    """Test exporting validation report with counts and errors."""
    report_file = tmp_path / "report.json"
    report = ValidationReport(
        valid_records=sample_records,
        errors=[
            ValidationError(field="email", message="Invalid email", source_file="bad.pdf")
        ],
    )
    result_path = export_validation_report(report, report_file)

    assert result_path.exists()
    with result_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["valid_record_count"] == 2
        assert data["error_count"] == 1
        assert len(data["errors"]) == 1
        assert data["errors"][0]["field"] == "email"


def test_generate_pdf_report(tmp_path: Path, sample_records):
    """Test PDF summary report creation and layout content."""
    pdf_file = tmp_path / "test_report.pdf"
    result_path = generate_pdf_report(sample_records, pdf_file)

    assert result_path.exists()
    assert result_path.stat().st_size > 0

    with pdfplumber.open(result_path) as pdf:
        assert len(pdf.pages) == 1
        text = pdf.pages[0].extract_text()
        assert "BayTaxPro — Customer Tax Summary Report" in text
        assert "Alice Smith" in text
        assert "Bob Jones" in text
        assert "Total" in text

