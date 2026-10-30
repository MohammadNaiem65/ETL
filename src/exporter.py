import csv
import json
import logging
from pathlib import Path
from decimal import Decimal
from typing import Any, List, Union

from src.models import ValidatedCustomerRecord, ValidationReport

logger = logging.getLogger(__name__)

CSV_FIELDNAMES = [
    "customer_name",
    "email",
    "tax_year",
    "income",
    "withholding",
    "source_file",
]

def _json_serial(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

#Export validated customer tax records to a CSV file.
def export_to_csv(
    records: List[ValidatedCustomerRecord],
    output_path: Union[str, Path],
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            for record in records:
                writer.writerow(record.to_dict())
        logger.info("Exported %d records to CSV: %s", len(records), path)
        return path
    except Exception as exc:
        logger.error("Failed to export records to CSV %s: %s", path, exc)
        raise

# Export validated customer tax records to a JSON file
def export_to_json(
    records: List[ValidatedCustomerRecord],
    output_path: Union[str, Path],
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        data = [record.to_dict() for record in records]
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=_json_serial)
        logger.info("Exported %d records to JSON: %s", len(records), path)
        return path
    except Exception as exc:
        logger.error("Failed to export records to JSON %s: %s", path, exc)
        raise

# Export validation report (valid record count, errors, details) to a JSON file
def export_validation_report(
    report: ValidationReport,
    output_path: Union[str, Path],
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, default=_json_serial)
        logger.info(
            "Exported validation report (%d valid, %d errors) to: %s",
            len(report.valid_records),
            len(report.errors),
            path,
        )
        return path
    except Exception as exc:
        logger.error("Failed to export validation report to %s: %s", path, exc)
        raise

