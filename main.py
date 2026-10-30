import argparse
import logging
from pathlib import Path
from typing import List, Optional, Sequence

from src.exporter import (
    export_to_csv,
    export_to_json,
    export_validation_report,
)
from src.html_extractor import extract_from_html
from src.models import RawCustomerRecord, ValidationReport
from src.pdf_extractor import extract_from_pdf
from src.pdf_generator import generate_pdf_report
from src.validator import validate_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("baytaxpro")

# Run the complete intake, extraction, validation, and export pipeline
def process_pipeline(
    input_files: Optional[Sequence[Path]] = None,
    input_dir: Optional[Path] = None,
    output_dir: Path = Path("data/output"),
) -> ValidationReport:
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Discover files
    if input_files is not None:
        file_paths = []
        for p in input_files:
            path = Path(p)
            if not path.exists():
                logger.warning("Input file does not exist: %s", path)
                continue
            if path.is_dir():
                logger.warning(
                    "Skipping directory in file input (use --dir instead): %s", path
                )
                continue
            if path.suffix.lower() not in {".html", ".htm", ".pdf"}:
                logger.warning("Skipping unsupported file format: %s", path)
                continue
            file_paths.append(path)
        file_paths = sorted(file_paths)
        logger.info(
            "Discovered %d candidate intake file(s) from input arguments",
            len(file_paths),
        )
    else:
        target_dir = input_dir if input_dir is not None else Path("data/input")
        if not target_dir.is_dir():
            logger.error("Input directory does not exist: %s", target_dir)
            return ValidationReport()

        file_paths = sorted(
            [
                p
                for p in target_dir.iterdir()
                if p.is_file() and p.suffix.lower() in {".html", ".htm", ".pdf"}
            ]
        )
        logger.info("Discovered %d candidate intake files in %s", len(file_paths), target_dir)

    # 2. Extract raw records
    raw_records: List[RawCustomerRecord] = []
    for file_path in file_paths:
        ext = file_path.suffix.lower()
        if ext in {".html", ".htm"}:
            raw_records.extend(extract_from_html(file_path))
        elif ext == ".pdf":
            raw_records.extend(extract_from_pdf(file_path))

    # 3. Validate extracted records
    report = validate_all(raw_records)

    # 4. Export validated records
    csv_path = output_dir / "records.csv"
    json_path = output_dir / "records.json"
    report_path = output_dir / "validation_report.json"
    pdf_report_path = output_dir / "tax_report.pdf"

    export_to_csv(report.valid_records, csv_path)
    export_to_json(report.valid_records, json_path)
    export_validation_report(report, report_path)
    generate_pdf_report(report.valid_records, pdf_report_path)

    # 5. CLI Summary (Protecting PII - aggregate metrics only)
    print("\n" + "=" * 55)
    print("               BAYTAXPRO PROCESSING SUMMARY")
    print("=" * 55)
    print(f"Total files scanned:          {len(file_paths)}")
    print(f"Valid records exported:       {len(report.valid_records)}")
    print(f"Validation errors identified: {len(report.errors)}")
    print("-" * 55)
    print(f"CSV Export:         {csv_path}")
    print(f"JSON Export:        {json_path}")
    print(f"Validation Report:  {report_path}")
    print(f"PDF Summary Report: {pdf_report_path}")

    if report.errors:
        print("\nIdentified Issues:")
        for err in report.errors:
            src = Path(err.source_file).name if err.source_file else "unknown"
            print(f"  - [{src}] {err.field or 'general'}: {err.message}")

    print("=" * 55 + "\n")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="BayTaxPro Tax Data Intake & Validation Pipeline"
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Path to one or more input documents (.html, .htm, .pdf)",
    )
    parser.add_argument(
        "--dir",
        "--input-dir",
        dest="input_dir",
        nargs="?",
        const=Path("data/input"),
        default=None,
        type=Path,
        help="Directory containing input documents (default: data/input when flag is passed without argument)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/output"),
        help="Path to output files directory (default: data/output)",
    )

    args = parser.parse_args()

    if args.input_dir is not None and args.files:
        parser.error("Cannot specify both file inputs and the '--dir' flag.")

    if args.input_dir is None and not args.files:
        parser.error(
            "No input files provided. Provide one or more file paths, or use '--dir' to process a directory."
        )

    if args.files:
        for p in args.files:
            if p.is_dir():
                parser.error(
                    f"'{p}' is a directory. Use '--dir {p}' to process directories."
                )

    process_pipeline(
        input_files=args.files if args.files else None,
        input_dir=args.input_dir,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
