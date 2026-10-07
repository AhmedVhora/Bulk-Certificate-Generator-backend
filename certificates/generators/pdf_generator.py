"""Pure ReportLab renderer for the one fixed certificate design."""

from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


def render_certificate_pdf(
    *, recipient_name: str, event_name: str, issue_date: date, issued_by: str
) -> bytes:
    """Return PDF bytes for one certificate without performing I/O."""
    buffer = BytesIO()
    page_width, page_height = landscape(A4)
    pdf = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    pdf.setStrokeColor(colors.HexColor("#1E3A5F"))
    pdf.setLineWidth(3)
    margin = 15 * mm
    pdf.rect(margin, margin, page_width - 2 * margin, page_height - 2 * margin)
    pdf.setLineWidth(0.7)
    pdf.rect(margin + 6 * mm, margin + 6 * mm, page_width - 42 * mm, page_height - 42 * mm)

    def centered(text: str, y: float, font: str, size: float, color: colors.Color) -> None:
        pdf.setFont(font, size)
        pdf.setFillColor(color)
        pdf.drawString((page_width - stringWidth(text, font, size)) / 2, y, text)

    centered("CERTIFICATE OF COMPLETION", page_height - 60 * mm, "Helvetica-Bold", 27, colors.HexColor("#1E3A5F"))
    centered("This certificate is proudly presented to", page_height - 88 * mm, "Helvetica", 13, colors.HexColor("#374151"))
    centered(recipient_name, page_height - 113 * mm, "Helvetica-Bold", 25, colors.HexColor("#8A5A00"))
    centered("for successfully participating in", page_height - 137 * mm, "Helvetica", 13, colors.HexColor("#374151"))
    centered(event_name, page_height - 159 * mm, "Helvetica-Bold", 18, colors.HexColor("#1E3A5F"))
    centered(f"Issued on {issue_date.strftime('%B %d, %Y')}", page_height - 190 * mm, "Helvetica", 11, colors.HexColor("#374151"))
    centered(issued_by, page_height - 211 * mm, "Helvetica-Bold", 12, colors.HexColor("#1E3A5F"))
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
