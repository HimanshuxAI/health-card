"""Build the final IJIRT-style DOCX from the manuscript and template."""
from __future__ import annotations

import json
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT = ROOT / "docs" / "paper" / "manuscript.md"
TEMPLATE = Path("/Users/himanshu/Downloads/ijirt_paperformat.docx")
OUTPUT = ROOT / "IJIRT_ABHA_Health_Card_Paper.docx"
REFERENCES = ROOT / "docs" / "paper" / "references.json"


def _clear_body(doc: Document) -> None:
    """Remove template instruction content while retaining document resources."""
    body = doc.element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def _set_columns(section, count: int, space_twips: int = 360) -> None:
    sect_pr = section._sectPr
    cols = sect_pr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols")
        sect_pr.append(cols)
    cols.set(qn("w:num"), str(count))
    cols.set(qn("w:space"), str(space_twips))
    if count > 1:
        cols.set(qn("w:equalWidth"), "1")


def _style_section(section, *, count: int = 1, start_type=None) -> None:
    if start_type is not None:
        section.start_type = start_type
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.header_distance = Inches(0.5)
    section.footer_distance = Inches(0.5)
    _set_columns(section, count, 360)


def _add_run(paragraph, text: str, *, size: float, bold: bool = False, italic: bool = False, color=None) -> None:
    run = paragraph.add_run(text)
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color


def _add_inline(paragraph, text: str, *, size: float, bold: bool = False, italic: bool = False) -> None:
    """Add basic bold/italic/code inline markdown."""
    text = text.replace("“", "“").replace("”", "”").replace("’", "’")
    pattern = re.compile(r"(\*\*(?P<bold>.+?)\*\*|\*(?P<italic>.+?)\*|`(?P<code>.+?)`)")
    pos = 0
    for match in pattern.finditer(text):
        if match.start() > pos:
            _add_run(paragraph, text[pos : match.start()], size=size, bold=bold, italic=italic)
        if match.group("bold"):
            _add_run(paragraph, match.group("bold"), size=size, bold=True, italic=italic)
        elif match.group("italic"):
            _add_run(paragraph, match.group("italic"), size=size, bold=bold, italic=True)
        elif match.group("code"):
            _add_run(paragraph, match.group("code"), size=size, bold=bold, italic=italic)
        pos = match.end()
    if pos < len(text):
        _add_run(paragraph, text[pos:], size=size, bold=bold, italic=italic)


def _add_paragraph(doc, text: str, *, size: float = 10, align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold: bool = False, italic: bool = False, space_after: int = 4, indent_first: float = 0.18) -> object:
    paragraph = doc.add_paragraph()
    paragraph.alignment = align
    pf = paragraph.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.0
    if indent_first:
        pf.first_line_indent = Inches(indent_first)
    _add_inline(paragraph, text, size=size, bold=bold, italic=italic)
    return paragraph


def _add_centered(doc, text: str, *, size: float, bold: bool = False, italic: bool = False, space_after: int = 0) -> object:
    return _add_paragraph(doc, text, size=size, align=WD_ALIGN_PARAGRAPH.CENTER, bold=bold, italic=italic, space_after=space_after, indent_first=0)


def _add_heading(doc, text: str, level: int) -> None:
    text = text.strip()
    if level == 2:
        paragraph = _add_centered(doc, text, size=10, bold=False, space_after=6)
        paragraph.paragraph_format.space_before = Pt(8)
        paragraph.paragraph_format.keep_with_next = True
    else:
        paragraph = _add_paragraph(doc, text, size=10, align=WD_ALIGN_PARAGRAPH.LEFT, italic=True, space_after=4, indent_first=0)
        paragraph.paragraph_format.space_before = Pt(4)
        paragraph.paragraph_format.keep_with_next = True


def _add_list_item(doc, text: str, ordered: bool, number: int | None = None) -> None:
    marker = f"{number}. " if ordered and number else "• "
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = paragraph.paragraph_format
    pf.left_indent = Inches(0.18)
    pf.first_line_indent = Inches(-0.18)
    pf.space_after = Pt(3)
    pf.line_spacing = 1.0
    _add_inline(paragraph, marker + text, size=10)


def _set_table_borders(table) -> None:
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "000000")
        borders.append(element)
    tbl_pr.append(borders)


def _add_table(doc, caption: str, rows: list[list[str]]) -> None:
    caption_paragraph = _add_centered(doc, caption, size=8, bold=True, space_after=2)
    caption_paragraph.paragraph_format.keep_with_next = True
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    _set_table_borders(table)
    for row_idx, row in enumerate(rows):
        for col_idx, value in enumerate(row):
            cell = table.cell(row_idx, col_idx)
            cell.text = ""
            paragraph = cell.paragraphs[0]
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT if row_idx > 0 else WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.line_spacing = 1.0
            _add_inline(paragraph, value, size=8, bold=(row_idx == 0))
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def _add_image(doc, caption: str, image_path: Path, *, fullwidth: bool = False) -> None:
    section = doc.add_section(WD_SECTION.CONTINUOUS)
    _style_section(section, count=1)
    picture_paragraph = doc.add_paragraph()
    picture_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    picture_paragraph.paragraph_format.space_after = Pt(2)
    picture_paragraph.paragraph_format.space_before = Pt(4)
    run = picture_paragraph.add_run()
    run.add_picture(str(image_path), width=Inches(6.25) if fullwidth else Inches(3.1))
    caption_paragraph = _add_centered(doc, caption, size=8, italic=False, space_after=8)
    caption_paragraph.paragraph_format.keep_together = True
    back = doc.add_section(WD_SECTION.CONTINUOUS)
    _style_section(back, count=2)


def _add_equation(doc, equation: str) -> None:
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(2.6)
    table.columns[1].width = Inches(0.45)
    left, right = table.rows[0].cells
    left.width = Inches(2.6)
    right.width = Inches(0.45)
    p = left.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    match = re.match(r"^(.*?)(\(\d+\))$", equation.strip())
    eq_text = match.group(1).strip() if match else equation
    number = match.group(2) if match else ""
    _add_inline(p, eq_text, size=9, italic=True)
    rp = right.paragraphs[0]
    rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rp.paragraph_format.space_after = Pt(2)
    _add_inline(rp, number, size=9)


def _parse_frontmatter(md: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\n(.*?)\n---\n", md, re.S)
    if not match:
        return {}, md
    data = {}
    for line in match.group(1).splitlines():
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data, md[match.end() :]


def _parse_rows(block: str) -> list[list[str]]:
    rows = []
    for line in block.strip().splitlines():
        if set(line.replace("|", "").strip()) <= {"-", " ", ":"}:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append(cells)
    return rows


def _blocks(md: str):
    """Split body into simple blocks: heading, paragraph, image, table, bullet, ordered, equation."""
    lines = md.splitlines()
    blocks: list[tuple[str, object]] = []
    paragraph: list[str] = []
    table: list[str] = []

    def flush_paragraph():
        if paragraph:
            blocks.append(("paragraph", " ".join(paragraph).strip()))
            paragraph.clear()

    def flush_table():
        if table:
            blocks.append(("table", _parse_rows("\n".join(table))))
            table.clear()

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            flush_paragraph()
            table.append(stripped)
            continue
        flush_table()
        if not stripped:
            flush_paragraph()
        elif stripped.startswith("## "):
            flush_paragraph()
            blocks.append(("heading2", stripped[3:].strip()))
        elif stripped.startswith("### "):
            flush_paragraph()
            blocks.append(("heading3", stripped[4:].strip()))
        elif stripped.startswith("!["):
            flush_paragraph()
            match = re.match(r"!\[(.*?)\]\((.*?)\)", stripped)
            blocks.append(("image", (match.group(1), ROOT / match.group(2))))
        elif stripped.startswith("- "):
            flush_paragraph()
            blocks.append(("bullet", stripped[2:]))
        elif re.match(r"^\d+\.\s", stripped):
            flush_paragraph()
            match = re.match(r"^(\d+)\.\s+(.*)$", stripped)
            blocks.append(("ordered", (int(match.group(1)), match.group(2))))
        elif re.match(r"^T_local\s*=", stripped):
            flush_paragraph()
            blocks.append(("equation", stripped))
        else:
            paragraph.append(stripped)
    flush_paragraph()
    flush_table()
    return blocks


def build() -> None:
    front, body = _parse_frontmatter(MANUSCRIPT.read_text(encoding="utf-8"))
    doc = Document(str(TEMPLATE))
    _clear_body(doc)

    # Word stores the first section in section[0]. Keep it one-column for the title/abstract block.
    _style_section(doc.sections[0], count=1, start_type=None)

    _add_centered(doc, front["title"], size=20, bold=False, space_after=8)
    _add_centered(doc, front["authors"], size=11, bold=False, space_after=4)
    _add_centered(doc, front["affiliations"], size=11, italic=True, space_after=10)

    abstract = doc.add_paragraph()
    abstract.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    abstract.paragraph_format.space_after = Pt(6)
    abstract.paragraph_format.line_spacing = 1.0
    _add_run(abstract, "Abstract—", size=9, bold=True, italic=True)
    _add_inline(abstract, front["abstract"], size=9)

    index = doc.add_paragraph()
    index.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    index.paragraph_format.space_after = Pt(6)
    index.paragraph_format.line_spacing = 1.0
    _add_run(index, "Index Terms—", size=9, bold=True, italic=True)
    _add_inline(index, front["index_terms"], size=9)

    # Start the two-column manuscript body on a continuous section.
    body_section = doc.add_section(WD_SECTION.CONTINUOUS)
    _style_section(body_section, count=2)

    for kind, payload in _blocks(body):
        if kind == "heading2":
            _add_heading(doc, payload, 2)
        elif kind == "heading3":
            _add_heading(doc, payload, 3)
        elif kind == "paragraph":
            _add_paragraph(doc, payload, size=10)
        elif kind == "bullet":
            _add_list_item(doc, payload, ordered=False)
        elif kind == "ordered":
            number, text = payload
            _add_list_item(doc, text, ordered=True, number=number)
        elif kind == "table":
            rows = payload
            _add_table(doc, "", rows)
        elif kind == "image":
            caption, image_path = payload
            fullwidth = image_path.name in {"architecture.png", "claim_flow.png"}
            _add_image(doc, caption, image_path, fullwidth=fullwidth)
        elif kind == "equation":
            _add_equation(doc, payload)

    doc.save(str(OUTPUT))
    print(f"Built {OUTPUT}")


def extract_paragraphs() -> list[str]:
    doc = Document(str(OUTPUT))
    return [p.text for p in doc.paragraphs if p.text.strip()]


def extract_tables() -> list[list[list[str]]]:
    doc = Document(str(OUTPUT))
    return [[[cell.text for cell in row.cells] for row in table.rows] for table in doc.tables]


def citation_report() -> dict:
    text = "\n".join(extract_paragraphs())
    refs = json.loads(REFERENCES.read_text())["references"]
    return {
        "references": len(refs),
        "missing_citations": [r["id"] for r in refs if f"[{r['id']}]" not in text],
        "tables": len(extract_tables()),
    }


if __name__ == "__main__":
    build()
    print(json.dumps(citation_report(), indent=2))
