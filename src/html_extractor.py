import logging
from pathlib import Path
from typing import Dict, Optional, Union
from bs4 import BeautifulSoup
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

# Extract raw key-value pairs from tables, paragraphs, and lists.
def _extract_pairs_from_soup(soup: BeautifulSoup) -> Dict[str, str]:
    pairs: Dict[str, str] = {}

    # Parse tables 
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True).lower().rstrip(":")
                value = cells[1].get_text(strip=True)
                if key and value:
                    pairs[key] = value

    # Parse paragraphs and list items
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
                pairs[key] = value
                continue

        if ":" in text:
            raw_key, _, raw_val = text.partition(":")
            key = raw_key.strip().lower()
            value = raw_val.strip()
            if key and value:
                pairs[key] = value

    return pairs

def extract_from_html(file_path: Union[str, Path]) -> RawCustomerRecord:
    path = Path(file_path)
    source_name = str(file_path)

    if not path.is_file():
        logger.warning("HTML file not found: %s", source_name)
        return RawCustomerRecord(source_file=source_name)

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = path.read_text(encoding="latin-1")
        except Exception as err:
            logger.error("Failed to read HTML file %s: %s", source_name, err)
            return RawCustomerRecord(source_file=source_name)
    except Exception as err:
        logger.error("Failed to read HTML file %s: %s", source_name, err)
        return RawCustomerRecord(source_file=source_name)

    try:
        soup = BeautifulSoup(content, "html.parser")
        raw_pairs = _extract_pairs_from_soup(soup)

        fields: Dict[str, Optional[str]] = {
            "customer_name": None,
            "email": None,
            "tax_year": None,
            "income": None,
            "withholding": None,
        }

        for raw_k, raw_v in raw_pairs.items():
            canonical_key = CANONICAL_FIELD_MAP.get(raw_k)
            if canonical_key and canonical_key in fields:
                fields[canonical_key] = raw_v

        return RawCustomerRecord(
            customer_name=fields["customer_name"],
            email=fields["email"],
            tax_year=fields["tax_year"],
            income=fields["income"],
            withholding=fields["withholding"],
            source_file=source_name,
        )
        
    except Exception as err:
        logger.error("Unexpected error parsing HTML file %s: %s", source_name, err)
        return RawCustomerRecord(source_file=source_name)
