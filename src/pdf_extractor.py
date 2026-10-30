import logging
import pdfplumber
from pathlib import Path
from typing import Dict, Optional, Union
from src.models import RawCustomerRecord

logger = logging.getLogger(__name__)

CANONICAL_FIELD_MAP: Dict[str, str] = {
    "customer name": "customer_name",
    "customer_name": "customer_name",
    "client name": "customer_name",
    "taxpayer name": "customer_name",
    "name": "customer_name",
    "email": "email",
    "email address": "email",
    "e-mail": "email",
    "tax year": "tax_year",
    "tax_year": "tax_year",
    "assessment year": "tax_year",
    "year": "tax_year",
    "gross income": "income",
    "total income": "income",
    "annual income": "income",
    "income": "income",
    "withholding amount": "withholding",
    "withholding_amount": "withholding",
    "tax withholding": "withholding",
    "tax withheld": "withholding",
    "withholding": "withholding",
}

# Prefixes sorted descending by length to match the longest candidate first
_SORTED_PREFIXES = sorted(CANONICAL_FIELD_MAP.keys(), key=len, reverse=True)


def _match_line_prefix(line: str) -> tuple[Optional[str], Optional[str]]:
    line_clean = line.strip()
    line_lower = line_clean.lower()

    for prefix in _SORTED_PREFIXES:
        # Exact match 
        if line_lower == prefix or line_lower == prefix + ":":
            return CANONICAL_FIELD_MAP[prefix], ""

        # Colon-separated
        if line_lower.startswith(prefix + ":"):
            val = line_clean[len(prefix) + 1 :].strip()
            return CANONICAL_FIELD_MAP[prefix], val

        # Space-separated
        if line_lower.startswith(prefix + " "):
            val = line_clean[len(prefix) + 1 :].strip()
            return CANONICAL_FIELD_MAP[prefix], val

    return None, None


def extract_from_pdf(file_path: Union[str, Path]) -> RawCustomerRecord:
    path = Path(file_path)
    source_name = str(file_path)

    if not path.is_file():
        logger.warning("PDF file not found: %s", source_name)
        return RawCustomerRecord(source_file=source_name)

    extracted_fields: Dict[str, Optional[str]] = {
        "customer_name": None,
        "email": None,
        "tax_year": None,
        "income": None,
        "withholding": None,
    }

    try:
        with pdfplumber.open(path) as pdf:
            # 1. First pass: try extracting tables across all pages
            for page in pdf.pages:
                tables = page.extract_tables() or []
                for table in tables:
                    for row in table:
                        if not row or len(row) < 2:
                            continue
                        cell_key = (row[0] or "").strip().lower().rstrip(":")
                        cell_val = (row[1] or "").strip()
                        canonical = CANONICAL_FIELD_MAP.get(cell_key)
                        if canonical and canonical in extracted_fields:
                            extracted_fields[canonical] = cell_val

            # 2. Second pass: for any field still missing, parse text lines
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                for line in text.splitlines():
                    canonical, val = _match_line_prefix(line)
                    if canonical and extracted_fields.get(canonical) is None:
                        extracted_fields[canonical] = val

        return RawCustomerRecord(
            customer_name=extracted_fields["customer_name"],
            email=extracted_fields["email"],
            tax_year=extracted_fields["tax_year"],
            income=extracted_fields["income"],
            withholding=extracted_fields["withholding"],
            source_file=source_name,
        )

    except Exception as exc:
        logger.error("Failed to parse PDF file %s: %s", source_name, exc)
        return RawCustomerRecord(source_file=source_name)

