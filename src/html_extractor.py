import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
from bs4 import BeautifulSoup, Tag
from src.constants import RECORD_FIELDS
from src.models import RawCustomerRecord

logger = logging.getLogger(__name__)

CANONICAL_FIELD_MAP = {
    "customer name": "customer_name",
    "customer_name": "customer_name",
    "name": "customer_name",
    "client name": "customer_name",
    "taxpayer name": "customer_name",
    "email": "email",
    "email address": "email",
    "e-mail": "email",
    "tax year": "tax_year",
    "tax_year": "tax_year",
    "year": "tax_year",
    "assessment year": "tax_year",
    "income": "income",
    "gross income": "income",
    "total income": "income",
    "annual income": "income",
    "withholding amount": "withholding",
    "withholding_amount": "withholding",
    "withholding": "withholding",
    "tax withholding": "withholding",
    "tax withheld": "withholding",
}

_RECORD_FIELDS = RECORD_FIELDS


def _detect_header_row(table: Tag) -> Optional[List[Optional[str]]]:
    """Return canonical field names if the table has a recognizable header row.

    A header row is identified as:
      1. The first ``<tr>`` inside ``<thead>``, OR
      2. The first ``<tr>`` in the table if *all* its cells are ``<th>``.

    Each header cell text is normalised and looked up in ``CANONICAL_FIELD_MAP``.
    If at least two headers are recognised, the table is treated as a
    multi-column data table and the list of canonical names (with ``None`` for
    unrecognised columns) is returned.  Otherwise ``None`` is returned.
    """
    thead = table.find("thead")
    header_row: Optional[Tag] = thead.find("tr") if thead else None
    if header_row is None:
        first_row = table.find("tr")
        if first_row and all(
            c.name == "th" for c in first_row.find_all(["td", "th"])
        ):
            header_row = first_row
    if header_row is None:
        return None

    headers: List[Optional[str]] = []
    for cell in header_row.find_all(["td", "th"]):
        raw = cell.get_text(strip=True).lower().rstrip(":")
        canonical = CANONICAL_FIELD_MAP.get(raw)
        headers.append(canonical)

    recognised = [h for h in headers if h is not None]
    return headers if len(recognised) >= 2 else None


def _extract_records_from_soup(
    soup: BeautifulSoup,
) -> List[Dict[str, Optional[str]]]:
    """Extract one or more sets of raw field values from the HTML document.

    Supports three HTML layouts:
      * **Multi-column data tables** — header row with field names across columns
        and one data row per record.
      * **Two-column key-value tables** — field name in column 0, value in column 1;
        produces a single record per table.
      * **Paragraphs / list items** — ``<strong>``/``<b>``/``<label>`` or colon-
        delimited key-value text; contributes to a single record.
    """
    all_records: List[Dict[str, Optional[str]]] = []
    # Collect key-value pairs from non-table elements and 2-col tables.
    kv_pairs: Dict[str, str] = {}

    # -- Tables --
    for table in soup.find_all("table"):
        headers = _detect_header_row(table)

        if headers is not None:
            # Multi-column data table — one record per data row.
            all_rows = table.find_all("tr")
            for row in all_rows:
                cells = row.find_all(["td", "th"])
                # Skip the header row itself.
                if any(c.name == "th" for c in cells):
                    continue
                record: Dict[str, Optional[str]] = {f: None for f in _RECORD_FIELDS}
                for idx, cell in enumerate(cells):
                    if idx >= len(headers) or headers[idx] is None:
                        continue
                    value = cell.get_text(strip=True)
                    record[headers[idx]] = value if value else None
                all_records.append(record)
        else:
            # Two-column key-value table (existing behaviour).
            for row in table.find_all("tr"):
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True).lower().rstrip(":")
                    value = cells[1].get_text(strip=True)
                    if key and value:
                        kv_pairs[key] = value

    # -- Paragraphs and list items --
    for element in soup.find_all(["p", "li"]):
        text = element.get_text(strip=True)
        if not text:
            continue

        strong = element.find(["strong", "b", "label"])
        if strong and strong.get_text(strip=True):
            label = strong.get_text(strip=True)
            key = label.lower().rstrip(":")
            # Remove the label part to extract the corresponding value
            value = element.get_text().replace(label, "", 1).strip().lstrip(":").strip()
            if key and value:
                kv_pairs[key] = value
                continue

        if ":" in text:
            raw_key, _, raw_val = text.partition(":")
            key = raw_key.strip().lower()
            value = raw_val.strip()
            if key and value:
                kv_pairs[key] = value

    # Build a record from accumulated kv_pairs (if any were found).
    if kv_pairs:
        record = {f: None for f in _RECORD_FIELDS}
        for raw_k, raw_v in kv_pairs.items():
            canonical = CANONICAL_FIELD_MAP.get(raw_k)
            if canonical and canonical in record:
                record[canonical] = raw_v
        all_records.append(record)

    return all_records


def extract_from_html(
    file_path: Union[str, Path],
) -> List[RawCustomerRecord]:
    """Extract customer records from an HTML file.

    Returns a list of ``RawCustomerRecord`` objects.  Multi-row data tables
    produce one record per row; all other layouts produce a single record.
    An empty list is never returned — on error or if the file is missing a
    single empty ``RawCustomerRecord`` is returned so callers can always
    inspect ``source_file``.
    """
    path = Path(file_path)
    source_name = str(file_path)

    if not path.is_file():
        logger.warning("HTML file not found: %s", source_name)
        return [RawCustomerRecord(source_file=source_name)]

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = path.read_text(encoding="latin-1")
        except Exception as err:
            logger.error("Failed to read HTML file %s: %s", source_name, err)
            return [RawCustomerRecord(source_file=source_name)]
    except Exception as err:
        logger.error("Failed to read HTML file %s: %s", source_name, err)
        return [RawCustomerRecord(source_file=source_name)]

    try:
        soup = BeautifulSoup(content, "html.parser")
        records_data = _extract_records_from_soup(soup)

        if not records_data:
            return [RawCustomerRecord(source_file=source_name)]

        results: List[RawCustomerRecord] = []
        for fields in records_data:
            results.append(
                RawCustomerRecord(
                    customer_name=fields.get("customer_name"),
                    email=fields.get("email"),
                    tax_year=fields.get("tax_year"),
                    income=fields.get("income"),
                    withholding=fields.get("withholding"),
                    source_file=source_name,
                )
            )
        return results

    except Exception as err:
        logger.error("Unexpected error parsing HTML file %s: %s", source_name, err)
        return [RawCustomerRecord(source_file=source_name)]
