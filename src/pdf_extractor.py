import logging
import pdfplumber
from pathlib import Path
from typing import Dict, List, Optional, Union
from src.constants import RECORD_FIELDS
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

_RECORD_FIELDS = RECORD_FIELDS

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


def _detect_header_row_pdf(first_row: list) -> Optional[List[Optional[str]]]:
    """Return canonical field names if the first row is a recognisable header."""
    headers: List[Optional[str]] = []
    for cell in first_row:
        raw = (cell or "").strip().lower().rstrip(":")
        headers.append(CANONICAL_FIELD_MAP.get(raw))

    recognised = [h for h in headers if h is not None]
    return headers if len(recognised) >= 2 else None


def extract_from_pdf(file_path: Union[str, Path]) -> List[RawCustomerRecord]:
    path = Path(file_path)
    source_name = str(file_path)

    if not path.is_file():
        logger.warning("PDF file not found: %s", source_name)
        return [RawCustomerRecord(source_file=source_name)]

    multi_col_records: List[Dict[str, Optional[str]]] = []
    kv_fields: Dict[str, Optional[str]] = {
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
                    if not table:
                        continue
                    headers = _detect_header_row_pdf(table[0])
                    if headers is not None:
                        # Multi-column data table
                        for row in table[1:]:
                            if not row:
                                continue
                            record: Dict[str, Optional[str]] = {f: None for f in _RECORD_FIELDS}
                            for idx, cell in enumerate(row):
                                if idx >= len(headers) or headers[idx] is None:
                                    continue
                                val = (cell or "").replace("\n", "").strip()
                                record[headers[idx]] = val if val else None
                            multi_col_records.append(record)
                    else:
                        for row in table:
                            if not row or len(row) < 2:
                                continue
                            cell_key = (row[0] or "").strip().lower().rstrip(":")
                            cell_val = (row[1] or "").strip()
                            canonical = CANONICAL_FIELD_MAP.get(cell_key)
                            if canonical and canonical in kv_fields:
                                kv_fields[canonical] = cell_val

            # If multi-column records were found, return them
            if multi_col_records:
                return [
                    RawCustomerRecord(
                        customer_name=r.get("customer_name"),
                        email=r.get("email"),
                        tax_year=r.get("tax_year"),
                        income=r.get("income"),
                        withholding=r.get("withholding"),
                        source_file=source_name,
                    )
                    for r in multi_col_records
                ]

            # 2. Second pass: for any field still missing, parse text lines
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                for line in text.splitlines():
                    canonical, val = _match_line_prefix(line)
                    if canonical and kv_fields.get(canonical) is None:
                        kv_fields[canonical] = val

        return [
            RawCustomerRecord(
                customer_name=kv_fields["customer_name"],
                email=kv_fields["email"],
                tax_year=kv_fields["tax_year"],
                income=kv_fields["income"],
                withholding=kv_fields["withholding"],
                source_file=source_name,
            )
        ]

    except Exception as exc:
        logger.error("Failed to parse PDF file %s: %s", source_name, exc)
        return [RawCustomerRecord(source_file=source_name)]

