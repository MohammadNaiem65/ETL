from datetime import datetime
from decimal import Decimal
import logging
from pathlib import Path
from typing import List, Union
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.models import ValidatedCustomerRecord

logger = logging.getLogger(__name__)

# Generate a clean, formatted PDF summary report of validated customer records
def generate_pdf_report(
    records: List[ValidatedCustomerRecord],
    output_path: Union[str, Path],
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        name="ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=6,
    )

    meta_style = ParagraphStyle(
        name="ReportMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=15,
    )

    footer_style = ParagraphStyle(
        name="ReportFooter",
        parent=styles["Italic"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#718096"),
        alignment=1,  # Center aligned
        spaceBefore=20,
    )

    content = []

    # Title & Metadata Header
    content.append(Paragraph("BayTaxPro — Customer Tax Summary Report", title_style))
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta_text = (
        f"<b>Generated:</b> {current_time} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Total Validated Records:</b> {len(records)}"
    )
    content.append(Paragraph(meta_text, meta_style))
    content.append(Spacer(1, 10))

    if not records:
        empty_style = ParagraphStyle(
            name="EmptyState",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            textColor=colors.HexColor("#718096"),
        )
        content.append(Paragraph("No validated records available to display.", empty_style))
    else:
        # Table Headers
        table_data = [
            ["Customer Name", "Email", "Tax Year", "Gross Income", "Withholding"]
        ]

        total_income = Decimal("0.00")
        total_withholding = Decimal("0.00")

        for r in records:
            total_income += r.income
            total_withholding += r.withholding
            table_data.append(
                [
                    r.customer_name,
                    r.email,
                    str(r.tax_year),
                    f"${r.income:,.2f}",
                    f"${r.withholding:,.2f}",
                ]
            )

        # Summary total row
        table_data.append(
            [
                "Total",
                "",
                "",
                f"${total_income:,.2f}",
                f"${total_withholding:,.2f}",
            ]
        )

        col_widths = [130, 180, 60, 85, 85]

        table_style = TableStyle(
            [
                # Header formatting
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                # Alignment
                ("ALIGN", (0, 0), (1, -1), "LEFT"),
                ("ALIGN", (2, 0), (2, -1), "CENTER"),
                ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
                # Body formatting
                ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -2), 9),
                ("TOPPADDING", (0, 1), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                # Alternating row colors
                *[
                    (
                        "BACKGROUND",
                        (0, i),
                        (-1, i),
                        colors.HexColor("#F7FAFC") if i % 2 == 0 else colors.white,
                    )
                    for i in range(1, len(records) + 1)
                ],
                # Total row formatting
                ("LINEABOVE", (0, -1), (-1, -1), 1.5, colors.HexColor("#2D3748")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EDF2F7")),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, -1), (-1, -1), 9),
                # Grid
                ("INNERGRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#E2E8F0")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
            ]
        )

        summary_table = Table(table_data, colWidths=col_widths)
        summary_table.setStyle(table_style)
        content.append(summary_table)

    content.append(Spacer(1, 20))
    content.append(
        Paragraph(
            "Confidential — Prepared exclusively for BayTaxPro intake and assessment.",
            footer_style,
        )
    )

    try:
        doc.build(content)
        logger.info("Generated PDF report with %d records at: %s", len(records), path)
        return path
    except Exception as exc:
        logger.error("Failed to generate PDF report %s: %s", path, exc)
        raise

