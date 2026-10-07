from pathlib import Path
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors


BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "generated"

OUTPUT_DIR.mkdir(exist_ok=True)


def generate_certificate(
    recipient_name: str,
    event_name: str,
    date: str,
    certificate_id: int
) -> str:

    safe_name = "".join(
        character if character.isalnum() or character in " -_"
        else "_"
        for character in recipient_name
    )

    filename = f"{certificate_id}_{safe_name}.pdf"
    output_path = OUTPUT_DIR / filename

    width, height = landscape(A4)

    pdf = canvas.Canvas(str(output_path), pagesize=(width, height))

    # Background
    pdf.setFillColor(colors.white)
    pdf.rect(0, 0, width, height, fill=1, stroke=0)

    # Outer border
    pdf.setStrokeColor(colors.HexColor("#1F3C5B"))
    pdf.setLineWidth(8)
    pdf.rect(
        25,
        25,
        width - 50,
        height - 50,
        fill=0,
        stroke=1
    )

    # Title
    pdf.setFillColor(colors.HexColor("#1F3C5B"))
    pdf.setFont("Helvetica-Bold", 30)

    pdf.drawCentredString(
        width / 2,
        height - 120,
        "CERTIFICATE OF PARTICIPATION"
    )

    # Subtitle
    pdf.setFillColor(colors.HexColor("#444444"))
    pdf.setFont("Helvetica", 16)

    pdf.drawCentredString(
        width / 2,
        height - 165,
        "This certificate is proudly presented to"
    )

    # Recipient name
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 28)

    pdf.drawCentredString(
        width / 2,
        height - 230,
        recipient_name
    )

    # Description
    pdf.setFillColor(colors.HexColor("#444444"))
    pdf.setFont("Helvetica", 15)

    pdf.drawCentredString(
        width / 2,
        height - 280,
        "for successfully participating in"
    )

    # Event
    pdf.setFillColor(colors.HexColor("#1F3C5B"))
    pdf.setFont("Helvetica-Bold", 21)

    pdf.drawCentredString(
        width / 2,
        height - 320,
        event_name
    )

    # Date
    pdf.setFillColor(colors.HexColor("#555555"))
    pdf.setFont("Helvetica", 13)

    pdf.drawCentredString(
        width / 2,
        100,
        f"Date: {date}"
    )

    pdf.save()

    return str(output_path)