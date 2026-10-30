# BayTaxPro

BayTaxPro is a Python CLI that extracts customer tax records from HTML and PDF documents, validates them into typed models, and exports the results as CSV, JSON, and a formatted PDF report.

## Features

**Import**

- HTML: `<table>` layouts and `<p>`/`<strong>` labeled summaries.
- PDF: structured table detection with line-by-line label matching as a fallback.
- Multiple records per document.
- Malformed, empty, or corrupted files are logged and reported instead of crashing the run.

**Validation**

- Required fields: `customer_name`, `email`, `tax_year`, `income`, `withholding`.
- Email format checks.
- Amount normalization: `$`, thousands separators, accounting negatives `(X)`, and `-$X`.
- Rejects non-numeric values and negative income or withholding.
- Tax year must be a 4-digit year between 1900 and 2100.
- Every issue is written to `validation_report.json`.

**Export**

- `records.csv` and `records.json` with all valid records.
- `tax_report.pdf`: styled summary table with alternating rows and totals.
- Input files are never modified.

## Project Structure

```text
BayTaxPro/
├── data/
│   ├── input/                 # Sample documents (valid, invalid, corrupted)
│   └── output/                # Generated exports (git-ignored)
├── src/
│   ├── constants.py           # Validation patterns and thresholds
│   ├── models.py              # Raw and validated record dataclasses
│   ├── html_extractor.py      # HTML parsing
│   ├── pdf_extractor.py       # PDF parsing
│   ├── validator.py           # Field validation
│   ├── exporter.py            # CSV, JSON, and validation report writers
│   └── pdf_generator.py       # ReportLab PDF report
├── tests/                     # pytest suite
├── main.py                    # CLI entry point
└── pyproject.toml             # Project metadata and dependencies
```

## Quick Start

Requires Python 3.13+. [`uv`](https://docs.astral.sh/uv/) is recommended.

```bash
uv sync                    # creates .venv and installs runtime + dev dependencies
uv run python main.py --dir
```

Without `uv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e . pytest
python main.py --dir
```

## Usage

```bash
# Process specific files
python main.py data/input/sample_valid_1.pdf data/input/sample_valid_2.html

# Process every .html/.htm/.pdf file in data/input
python main.py --dir

# Custom input and output directories
python main.py --dir custom/input --output-dir custom/output
```

| Option                       | Description                                                          |
| ---------------------------- | -------------------------------------------------------------------- |
| `files ...`                  | One or more input documents (`.html`, `.htm`, `.pdf`)                |
| `--dir`, `--input-dir [DIR]` | Process a directory (defaults to `data/input` when no path is given) |
| `--output-dir DIR`           | Output directory (default: `data/output`)                            |

### Sample output

Running `python main.py --dir` against the bundled samples:

```text
=======================================================
               BAYTAXPRO PROCESSING SUMMARY
=======================================================
Total files scanned:          8
Valid records exported:       7
Validation errors identified: 9
-------------------------------------------------------
CSV Export:         data/output/records.csv
JSON Export:        data/output/records.json
Validation Report:  data/output/validation_report.json
PDF Summary Report: data/output/tax_report.pdf

Identified Issues:
  - [corrupted_tax_doc.pdf] customer_name: Missing required field: customer_name
  - [corrupted_tax_doc.pdf] email: Missing required field: email
  - [corrupted_tax_doc.pdf] tax_year: Missing required field: tax_year
  - [corrupted_tax_doc.pdf] income: Missing required field: income
  - [corrupted_tax_doc.pdf] withholding: Missing required field: withholding
  - [customers_table.html] email: Missing required field: email
  - [customers_table.html] income: Negative income value is not permitted: -1250.00
  - [sample_negative_income_missing_email.pdf] email: Missing required field: email
  - [sample_negative_income_missing_email.pdf] income: Negative income value is not permitted: -15200.00
=======================================================
```

## Testing

```bash
uv run pytest -v
```

The suite covers:

- HTML (table and paragraph layouts) and PDF extraction
- Missing and corrupted files
- Missing required fields, invalid emails, and non-numeric amounts
- Negative income and withholding
- Malformed and out-of-range tax years
- CSV, JSON, and PDF export output
- End-to-end CLI runs
