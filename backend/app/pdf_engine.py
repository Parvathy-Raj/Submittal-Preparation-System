from dataclasses import dataclass
from io import BytesIO
from typing import Iterable
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

try:
    pdfmetrics.registerFont(TTFont("Calibri-Light", "/usr/share/fonts/windows/calibril.ttf"))
except Exception:
    pass

try:
    pdfmetrics.registerFont(TTFont("Impact", "/usr/share/fonts/windows/impact.ttf"))
except Exception:
    pass


def _available_font(requested: str) -> str:
    """Use the approved font when installed, with a safe deployment fallback."""
    if requested in pdfmetrics.getRegisteredFontNames():
        return requested
    if requested == "Impact":
        return "Helvetica-Bold"
    if requested == "Calibri-Light":
        return "Helvetica"
    return "Helvetica"


def default_field_map(kind: str) -> dict:
    """Fallback template coordinates used when an uploaded template has no JSON map.

    The uploaded PDF remains the base design; these defaults only place dynamic
    text over the approved cover/index/divider templates.
    """
    if kind == "cover":
        return {
            "__masks__": [
                {"page": 0, "x": 72, "y": 95, "width": 470, "height": 610, "color": "#FFFFFF"},
            ],
            "__cover_auto__": {"page": 0, "x": 306, "max_width": 455},
        }
    if kind == "index":
        return {
            "__index_table__": {
                "page": 0,
                "mask": True,
                "mask_x": 32,
                "mask_y": 58,
                "mask_width": 530,
                "mask_height": 650,
                "x": 44,
                "top": 690,
                "width": 492,
                "sr_width": 82,
                "header_height": 58,
                "row_height": 49,
                "max_rows": 10,
                "heading_font": "Impact",
                "heading_size": 27,
                "sr_heading_size": 25,
                "font": "Helvetica-Bold",
                "font_size": 14,
                "heading_color": "#333333",
                "color": "#000000",
                "line_color": "#000000",
                "line_width": 0.7,
                "title_label": "TABLE OF CONTENTS",
                "sr_label": "SR NO.",
            }
        }
    if kind == "divider":
        return {
            "__masks__": [
                {"page": 0, "x": 50, "y": 330, "width": 500, "height": 115, "color": "#FFFFFF"},
            ],
            "section_title": {"page": 0, "x": 297.5, "y": 385, "font": "Helvetica-Bold", "font_size": 28, "max_width": 460, "align": "center", "color": "#000000"},
        }
    return {}


def effective_field_map(kind: str, field_map: dict | None) -> dict:
    return field_map if field_map else default_field_map(kind)


@dataclass
class FileEntry:
    name: str
    content: bytes


@dataclass
class Section:
    title: str
    files: list[FileEntry | bytes]


def _fit_text(text: str, font: str, size: float, max_width: float) -> tuple[str, float]:
    text = str(text)
    while max_width and size > 6.5 and stringWidth(text, font, size) > max_width:
        size -= 0.25
    if max_width and stringWidth(text, font, size) > max_width:
        while text and stringWidth(f"{text}...", font, size) > max_width:
            text = text[:-1]
        text = f"{text}..." if text else ""
    return text, size


def _wrap_text(text: str, font: str, size: float, max_width: float, max_lines: int) -> list[str]:
    words = str(text).split()
    if not words:
        return []
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or stringWidth(candidate, font, size) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
            if len(lines) >= max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and len(" ".join(words)) > len(" ".join(lines)):
        fitted, _ = _fit_text(lines[-1], font, size, max_width)
        lines[-1] = fitted
    return lines


def _wrapped_lines_that_fit(text: str, font: str, max_size: float, min_size: float, max_width: float, max_lines: int) -> tuple[list[str], float]:
    text = str(text).upper().strip()
    size = max_size
    while size >= min_size:
        lines = _wrap_text(text, font, size, max_width, max_lines)
        if lines and len(lines) <= max_lines and all(stringWidth(line, font, size) <= max_width for line in lines):
            return lines, size
        size -= 0.5
    return _wrap_text(text, font, min_size, max_width, max_lines), min_size


def _draw_centered_lines(pdf: canvas.Canvas, x: float, y: float, lines: list[str], font: str, size: float, color: str, line_height: float) -> float:
    pdf.setFillColor(HexColor(color))
    pdf.setFont(font, size)
    current_y = y
    for line in lines:
        pdf.drawCentredString(x, current_y, line)
        current_y -= line_height
    return current_y


def _draw_cover_auto(pdf: canvas.Canvas, values: dict[str, str], spec: dict) -> None:
    x = float(spec.get("x", 306))
    max_width = float(spec.get("max_width", 455))
    title_font = _available_font("Impact")
    body_font = _available_font("Impact")
    role_font = _available_font("Helvetica-Bold")
    small_font = _available_font("Helvetica")

    heading = str(values.get("cover_heading") or f"MATERIAL SUBMITTAL FOR {values.get('material_description', '')}").upper()
    heading_lines, heading_size = _wrapped_lines_that_fit(heading, title_font, 20, 13, max_width, 2)
    _draw_centered_lines(pdf, x, 656, heading_lines, title_font, heading_size, "#0B2A64", heading_size + 4)

    project = str(values.get("project_name", "")).upper()
    project_lines, project_size = _wrapped_lines_that_fit(project, body_font, 48, 30, max_width, 3)
    project_line_height = project_size + 7
    project_top = 575
    project_bottom = _draw_centered_lines(pdf, x, project_top, project_lines, body_font, project_size, "#FF0000", project_line_height)

    parties = []
    for index in range(1, 5):
        name = str(values.get(f"party_{index}_name", "")).strip()
        role = str(values.get(f"party_{index}_role", "")).strip()
        if name:
            parties.append((name.upper(), role.upper()))

    submitted_name = str(values.get("submitted_by", "")).upper().strip()
    submitted_role = str(values.get("submitted_by_role", "")).upper().strip()
    submitted_lines, submitted_size = _wrapped_lines_that_fit(submitted_name, body_font, 20, 14, max_width, 2)
    submitted_line_height = submitted_size + 4
    submitted_block_height = 16 + 8 + len(submitted_lines) * submitted_line_height + 18 + 30
    submitted_top = 178
    party_bottom_limit = submitted_top + submitted_block_height - 12
    party_top = min(project_bottom - 28, 420)
    available_party_height = max(95, party_top - party_bottom_limit)

    selected_party_size = 22
    selected_blocks: list[tuple[list[str], float, str]] = []
    for size in [22, 21, 20, 19, 18, 17, 16, 15, 14]:
        blocks = []
        total_height = 0.0
        for name, role in parties:
            lines = _wrap_text(name, body_font, size, max_width, 2)
            line_height = size + 4
            block_height = len(lines) * line_height + 12 + 13
            blocks.append((lines, line_height, role))
            total_height += block_height
        if parties:
            total_height += max(0, len(parties) - 1) * 6
        if total_height <= available_party_height or size == 14:
            selected_party_size = size
            selected_blocks = blocks
            break

    current_y = party_top
    for lines, line_height, role in selected_blocks:
        current_y = _draw_centered_lines(pdf, x, current_y, lines, body_font, selected_party_size, "#3B3B3B", line_height)
        role_y = current_y + 1
        pdf.setFillColor(HexColor("#000000"))
        pdf.setFont(role_font, 9.5)
        pdf.drawCentredString(x, role_y, role)
        current_y = role_y - 22

    label_y = min(178, current_y - 2) if parties else 185
    label_y = max(label_y, 152)
    label = "SUBMITTED BY:"
    pdf.setFillColor(HexColor("#0057B8"))
    pdf.setFont(_available_font("Helvetica-Oblique"), 10)
    pdf.drawCentredString(x, label_y, label)
    label_width = stringWidth(label, _available_font("Helvetica-Oblique"), 10)
    pdf.setLineWidth(0.6)
    pdf.line(x - label_width / 2, label_y - 2, x + label_width / 2, label_y - 2)

    submitted_name_top = label_y - 28
    submitted_bottom = _draw_centered_lines(pdf, x, submitted_name_top, submitted_lines, body_font, submitted_size, "#3B3B3B", submitted_line_height)
    if submitted_role:
        pdf.setFillColor(HexColor("#000000"))
        pdf.setFont(role_font, 10)
        pdf.drawCentredString(x, submitted_bottom - 1, submitted_role)

    footer = str(values.get("footer_reference", "")).upper()
    footer, footer_size = _fit_text(footer, small_font, 10, max_width)
    pdf.setFillColor(HexColor("#0057B8"))
    pdf.setFont(small_font, footer_size)
    pdf.drawCentredString(x, 96, footer)


def _page_count(content: bytes) -> int:
    reader = PdfReader(BytesIO(content))
    if reader.is_encrypted and reader.decrypt("") == 0:
        raise ValueError("Password-protected PDFs are not supported")
    return len(reader.pages)


def _normalise_file(entry: FileEntry | bytes, index: int) -> FileEntry:
    if isinstance(entry, FileEntry):
        return entry
    return FileEntry(name=f"Document {index + 1}", content=entry)


def _overlay(template: bytes, values: dict[str, str], field_map: dict) -> bytes:
    source = PdfReader(BytesIO(template))
    writer = PdfWriter()
    for page_index, page in enumerate(source.pages):
        width, height = float(page.mediabox.width), float(page.mediabox.height)
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=(width, height), pageCompression=1)
        for mask in field_map.get("__masks__", []):
            if int(mask.get("page", 0)) == page_index:
                pdf.setFillColor(HexColor(mask.get("color", "#FFFFFF")))
                pdf.rect(float(mask["x"]), float(mask["y"]), float(mask["width"]), float(mask["height"]), stroke=0, fill=1)
        cover_auto = field_map.get("__cover_auto__")
        if cover_auto is not None and int(cover_auto.get("page", 0)) == page_index:
            _draw_cover_auto(pdf, values, cover_auto)
        for field, spec in field_map.items():
            if field.startswith("__") or int(spec.get("page", 0)) != page_index:
                continue
            text = str(spec.get("literal", values.get(field, "")))
            if not text:
                continue
            font = _available_font(spec.get("font", "Helvetica"))
            size = float(spec.get("font_size", 10))
            max_width = float(spec.get("max_width", 0))
            if spec.get("uppercase"):
                text = text.upper()
            while max_width and not spec.get("wrap") and size > 7 and stringWidth(text, font, size) > max_width:
                size -= 0.5
            pdf.setFillColor(HexColor(spec.get("color", "#000000")))
            pdf.setFont(font, size)
            x, y = float(spec["x"]), float(spec["y"])
            if spec.get("wrap") and max_width:
                lines = _wrap_text(text, font, size, max_width, int(spec.get("max_lines", 2)))
                line_height = float(spec.get("line_height", size * 1.15))
                start_y = y
                for line_index, line in enumerate(lines):
                    line_y = start_y - line_height * line_index
                    if spec.get("align") == "center":
                        pdf.drawCentredString(x, line_y, line)
                    else:
                        pdf.drawString(x, line_y, line)
                continue
            if spec.get("align") == "center":
                pdf.drawCentredString(x, y, text)
                left = x - stringWidth(text, font, size) / 2
            else:
                pdf.drawString(x, y, text)
                left = x
            if spec.get("underline"):
                pdf.setLineWidth(float(spec.get("underline_width", 0.7)))
                pdf.line(left, y - 2, left + stringWidth(text, font, size), y - 2)
        table = field_map.get("__index_table__")
        rows = values.get("__index_rows__", [])
        if table is not None and int(table.get("page", 0)) == page_index and isinstance(rows, list):
            mask = table.get("mask", True)
            if mask:
                pdf.setFillColor(HexColor(table.get("mask_color", "#FFFFFF")))
                pdf.rect(float(table.get("mask_x", 35)), float(table.get("mask_y", 45)), float(table.get("mask_width", width - 96)), float(table.get("mask_height", height - 127)), stroke=0, fill=1)
            table_x = float(table.get("x", 35))
            table_top = float(table.get("top", height - 102))
            table_width = float(table.get("width", width - 96))
            sr_width = float(table.get("sr_width", 86))
            header_height = float(table.get("header_height", 65))
            default_row_height = float(table.get("row_height", 61))
            row_count = max(1, len(rows))
            table_bottom = float(table.get("bottom", max(45, table_top - header_height - default_row_height * row_count)))
            row_height = float(table.get("row_height", (table_top - header_height - table_bottom) / row_count))
            table_height = header_height + row_height * row_count
            table_bottom = table_top - table_height
            table_right = table_x + table_width
            sr_x = table_right - sr_width
            line_color = HexColor(table.get("line_color", "#000000"))
            pdf.setLineWidth(float(table.get("line_width", 0.6)))
            pdf.setStrokeColor(line_color)
            pdf.rect(table_x, table_bottom, table_width, table_height, stroke=1, fill=0)
            pdf.line(sr_x, table_bottom, sr_x, table_top)
            header_bottom = table_top - header_height
            pdf.line(table_x, header_bottom, table_right, header_bottom)
            for index in range(1, row_count):
                y_line = header_bottom - row_height * index
                pdf.line(table_x, y_line, table_right, y_line)

            heading_font = _available_font(table.get("heading_font", "Impact"))
            row_font = _available_font(table.get("font", "Helvetica-Bold"))
            heading_size = float(table.get("heading_size", 28))
            sr_heading_size = float(table.get("sr_heading_size", 26))
            row_size = float(table.get("font_size", 15))
            header_y = header_bottom + (header_height - heading_size) / 2 + 3
            pdf.setFillColor(HexColor(table.get("heading_color", "#333333")))
            pdf.setFont(heading_font, heading_size)
            pdf.drawString(table_x + float(table.get("title_padding", 8)), header_y, table.get("title_label", "TABLE OF CONTENTS"))
            pdf.setFont(heading_font, sr_heading_size)
            pdf.drawCentredString(sr_x + sr_width / 2, header_y, table.get("sr_label", "SR NO."))

            pdf.setFillColor(HexColor(table.get("color", "#000000")))
            for row_index, row in enumerate(rows):
                y_center = header_bottom - row_height * row_index - row_height / 2
                y_text = y_center - row_size / 2 + 3
                title, fitted_size = _fit_text(str(row.get("title", "")).upper(), row_font, row_size, sr_x - table_x - 18)
                pdf.setFont(row_font, fitted_size)
                pdf.drawString(table_x + float(table.get("row_padding", 8)), y_text, title)
                pdf.setFont(row_font, row_size)
                pdf.drawCentredString(sr_x + sr_width / 2, y_text, str(row.get("number", "")))
        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        overlay_page = PdfReader(buffer).pages[0]
        page.merge_page(overlay_page)
        writer.add_page(page)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def _append(writer: PdfWriter, content: bytes) -> None:
    reader = PdfReader(BytesIO(content))
    if reader.is_encrypted and reader.decrypt("") == 0:
        raise ValueError("Password-protected PDFs are not supported")
    for page in reader.pages:
        writer.add_page(page)


def _index_table_config(field_map: dict) -> dict:
    table = field_map.get("__index_table__", {})
    return table if isinstance(table, dict) else {}


def _rows_per_index_page(template: bytes, field_map: dict) -> int:
    table = _index_table_config(field_map)
    if "max_rows" in table:
        return max(1, int(table["max_rows"]))
    reader = PdfReader(BytesIO(template))
    first_page = reader.pages[int(table.get("page", 0))]
    height = float(first_page.mediabox.height)
    start_y = float(table.get("y", height - 175))
    min_y = float(table.get("min_y", 90))
    row_gap = float(table.get("row_gap", 20))
    return max(1, int((start_y - min_y) // row_gap) - 1)


def _index_chunks(rows: list[dict], per_page: int) -> list[list[dict]]:
    return [rows[index:index + per_page] for index in range(0, len(rows), per_page)] or [[]]


def _overlay_index(template: bytes, values: dict[str, str], field_map: dict, rows: list[dict]) -> bytes:
    per_page = _rows_per_index_page(template, field_map)
    writer = PdfWriter()
    for page_number, chunk in enumerate(_index_chunks(rows, per_page), 1):
        page_values = values | {
            "__index_rows__": chunk,
            "index_page_number": str(page_number),
            "index_page_count": str(len(_index_chunks(rows, per_page))),
        }
        for row_index, row in enumerate(chunk, 1):
            page_values[f"index_number_{row_index}"] = str(row.get("number", ""))
            page_values[f"index_item_{row_index}"] = str(row.get("title", ""))
            page_values[f"index_page_{row_index}"] = str(row.get("page", ""))
        _append(writer, _overlay(template, page_values, field_map))
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def _build_index_rows(sections: list[Section]) -> list[dict]:
    return [{"level": 0, "number": str(section_index), "title": section.title, "page": ""} for section_index, section in enumerate(sections, 1)]


def assemble(cover: tuple[bytes, dict], index: tuple[bytes, dict], divider: tuple[bytes, dict], values: dict[str, str], sections: Iterable[Section]) -> bytes:
    sections = list(sections)
    writer = PdfWriter()
    cover_pdf = _overlay(cover[0], values, cover[1])
    _append(writer, cover_pdf)
    index_rows = _build_index_rows(sections)
    index_values = values | {"section_count": str(len(sections)), "index_items": " | ".join(s.title for s in sections)}
    _append(writer, _overlay_index(index[0], index_values, index[1] | {"__index_table__": _index_table_config(index[1])}, index_rows))
    for section in sections:
        _append(writer, _overlay(divider[0], values | {"section_title": section.title}, divider[1]))
        for file_index, raw_file in enumerate(section.files):
            entry = _normalise_file(raw_file, file_index)
            _append(writer, entry.content)
    result = BytesIO()
    writer.write(result)
    return result.getvalue()

