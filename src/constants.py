import re

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

MIN_TAX_YEAR = 1900
MAX_TAX_YEAR = 2100

RECORD_FIELDS = (
    "customer_name",
    "email",
    "tax_year",
    "income",
    "withholding",
)

CSV_FIELDNAMES = [
    *RECORD_FIELDS,
    "source_file",
]


