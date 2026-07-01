from io import BytesIO
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from app.pdf_engine import Section, assemble


def page(text: str, size=(612, 792)) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=size)
    pdf.drawString(30, size[1] - 30, text)
    pdf.save()
    return buffer.getvalue()


def test_assembly_preserves_source_page_size_and_order():
    template = page("approved template")
    source = page("controlled source", (420, 595))
    result = assemble(
        (template, {"project_name": {"page": 0, "x": 30, "y": 700}}),
        (template, {}),
        (template, {"section_title": {"page": 0, "x": 30, "y": 700}}),
        {"project_name": "Test Project"},
        [Section("Datasheets", [source])],
    )
    pages = PdfReader(BytesIO(result)).pages
    assert len(pages) == 4
    assert float(pages[-1].mediabox.width) == 420
    assert float(pages[-1].mediabox.height) == 595
