"""Build the final IJIRT-style DOCX from the manuscript and base document."""
from __future__ import annotations

import json
import os
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
# Base document: env var → committed copy → old Downloads location (fallback)
BASE_DOCX = (
    Path(os.environ["IJIRT_BASE_DOCX"])
    if "IJIRT_BASE_DOCX" in os.environ
    else (ROOT / "docs" / "paper" / "ijirt_base.docx" if (ROOT / "docs" / "paper" / "ijirt_base.docx").exists() else Path("/Users/himanshu/Downloads/ijirt_paperformat.docx"))
)
OUTPUT = ROOT / "IJIRT_ABHA_Health_Card_Paper.docx"
REFERENCES = ROOT / "docs" / "paper" / "references.json"

COLUMN_WIDTH_IN = 3.0  # IJIRT column measure (US Letter, 1in margins, 0.5in gutter)


def _clear_body(doc: Document) -> None:
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


def _create_independent_header_footer(section, is_first_section: bool) -> None:
    """Create independent header/footer parts for a section."""
    if not is_first_section:
        # For subsequent sections, we need to create new header/footer parts
        # by breaking the link to previous
        section.header.is_linked_to_previous = False
        section.footer.is_linked_to_previous = False
        # Force creation of new header/footer parts by accessing them
        _ = section.header.part
        _ = section.footer.part

    # Now clear and populate
    for part_el in (section.header._element, section.footer._element):
        for child in list(part_el):
            if child.tag.endswith('}p') or child.tag.endswith('}tbl'):
                part_el.remove(child)

    # Header paragraph
    hdr_p = OxmlElement("w:p")
    hdr_pPr = OxmlElement("w:pPr")
    hdr_jc = OxmlElement("w:jc")
    hdr_jc.set(qn("w:val"), "right")
    hdr_pPr.append(hdr_jc)
    hdr_spacing = OxmlElement("w:spacing")
    hdr_spacing.set(qn("w:before"), "0")
    hdr_spacing.set(qn("w:after"), "0")
    hdr_spacing.set(qn("w:line"), "240")
    hdr_spacing.set(qn("w:lineRule"), "auto")
    hdr_pPr.append(hdr_spacing)
    hdr_p.append(hdr_pPr)
    hdr_r = OxmlElement("w:r")
    hdr_rPr = OxmlElement("w:rPr")
    hdr_rFonts = OxmlElement("w:rFonts")
    hdr_rFonts.set(qn("w:ascii"), "Arial")
    hdr_rFonts.set(qn("w:hAnsi"), "Arial")
    hdr_rFonts.set(qn("w:cs"), "Arial")
    hdr_rFonts.set(qn("w:eastAsia"), "Arial")
    hdr_rPr.append(hdr_rFonts)
    hdr_sz = OxmlElement("w:sz")
    hdr_sz.set(qn("w:val"), "18")
    hdr_rPr.append(hdr_sz)
    hdr_r.append(hdr_rPr)
    hdr_t = OxmlElement("w:t")
    hdr_t.text = "© May 2020 | IJIRT | Volume 6 Issue 12 | ISSN: 2349-6002"
    hdr_r.append(hdr_t)
    hdr_p.append(hdr_r)
    section.header._element.append(hdr_p)

    # Footer paragraph
    ftr_p = OxmlElement("w:p")
    ftr_pPr = OxmlElement("w:pPr")
    ftr_spacing = OxmlElement("w:spacing")
    ftr_spacing.set(qn("w:before"), "0")
    ftr_spacing.set(qn("w:after"), "0")
    ftr_spacing.set(qn("w:line"), "240")
    ftr_spacing.set(qn("w:lineRule"), "auto")
    ftr_pPr.append(ftr_spacing)
    ftr_p.append(ftr_pPr)

    # Left: IJIRT 140001
    ftr_r1 = OxmlElement("w:r")
    ftr_r1Pr = OxmlElement("w:rPr")
    ftr_r1Fonts = OxmlElement("w:rFonts")
    ftr_r1Fonts.set(qn("w:ascii"), "Times New Roman")
    ftr_r1Fonts.set(qn("w:hAnsi"), "Times New Roman")
    ftr_r1Fonts.set(qn("w:cs"), "Times New Roman")
    ftr_r1Fonts.set(qn("w:eastAsia"), "Times New Roman")
    ftr_r1Pr.append(ftr_r1Fonts)
    ftr_r1Sz = OxmlElement("w:sz")
    ftr_r1Sz.set(qn("w:val"), "16")
    ftr_r1Pr.append(ftr_r1Sz)
    ftr_r1B = OxmlElement("w:b")
    ftr_r1Pr.append(ftr_r1B)
    ftr_r1.append(ftr_r1Pr)
    ftr_t1 = OxmlElement("w:t")
    ftr_t1.text = "IJIRT 140001"
    ftr_r1.append(ftr_t1)
    ftr_p.append(ftr_r1)

    # Tab 1
    ftr_rTab1 = OxmlElement("w:r")
    ftr_rTab1Pr = OxmlElement("w:rPr")
    ftr_rTab1Fonts = OxmlElement("w:rFonts")
    ftr_rTab1Fonts.set(qn("w:ascii"), "Times New Roman")
    ftr_rTab1Fonts.set(qn("w:hAnsi"), "Times New Roman")
    ftr_rTab1Fonts.set(qn("w:cs"), "Times New Roman")
    ftr_rTab1Fonts.set(qn("w:eastAsia"), "Times New Roman")
    ftr_rTab1Pr.append(ftr_rTab1Fonts)
    ftr_rTab1Sz = OxmlElement("w:sz")
    ftr_rTab1Sz.set(qn("w:val"), "16")
    ftr_rTab1Pr.append(ftr_rTab1Sz)
    ftr_rTab1B = OxmlElement("w:b")
    ftr_rTab1Pr.append(ftr_rTab1B)
    ftr_rTab1.append(ftr_rTab1Pr)
    ftr_tab1 = OxmlElement("w:tab")
    ftr_rTab1.append(ftr_tab1)
    ftr_p.append(ftr_rTab1)

    # Centre: Journal name
    ftr_r2 = OxmlElement("w:r")
    ftr_r2Pr = OxmlElement("w:rPr")
    ftr_r2Fonts = OxmlElement("w:rFonts")
    ftr_r2Fonts.set(qn("w:ascii"), "Times New Roman")
    ftr_r2Fonts.set(qn("w:hAnsi"), "Times New Roman")
    ftr_r2Fonts.set(qn("w:cs"), "Times New Roman")
    ftr_r2Fonts.set(qn("w:eastAsia"), "Times New Roman")
    ftr_r2Pr.append(ftr_r2Fonts)
    ftr_r2Sz = OxmlElement("w:sz")
    ftr_r2Sz.set(qn("w:val"), "16")
    ftr_r2Pr.append(ftr_r2Sz)
    ftr_r2B = OxmlElement("w:b")
    ftr_r2Pr.append(ftr_r2B)
    ftr_r2.append(ftr_r2Pr)
    ftr_t2 = OxmlElement("w:t")
    ftr_t2.text = "INTERNATIONAL JOURNAL OF INNOVATIVE RESEARCH IN TECHNOLOGY"
    ftr_r2.append(ftr_t2)
    ftr_p.append(ftr_r2)

    # Tab 2
    ftr_rTab2 = OxmlElement("w:r")
    ftr_rTab2Pr = OxmlElement("w:rPr")
    ftr_rTab2Fonts = OxmlElement("w:rFonts")
    ftr_rTab2Fonts.set(qn("w:ascii"), "Times New Roman")
    ftr_rTab2Fonts.set(qn("w:hAnsi"), "Times New Roman")
    ftr_rTab2Fonts.set(qn("w:cs"), "Times New Roman")
    ftr_rTab2Fonts.set(qn("w:eastAsia"), "Times New Roman")
    ftr_rTab2Pr.append(ftr_rTab2Fonts)
    ftr_rTab2Sz = OxmlElement("w:sz")
    ftr_rTab2Sz.set(qn("w:val"), "16")
    ftr_rTab2Pr.append(ftr_rTab2Sz)
    ftr_rTab2B = OxmlElement("w:b")
    ftr_rTab2Pr.append(ftr_rTab2B)
    ftr_rTab2.append(ftr_rTab2Pr)
    ftr_tab2 = OxmlElement("w:tab")
    ftr_rTab2.append(ftr_tab2)
    ftr_p.append(ftr_rTab2)

    # Right: PAGE field
    ftr_r3 = OxmlElement("w:r")
    ftr_r3Pr = OxmlElement("w:rPr")
    ftr_r3Fonts = OxmlElement("w:rFonts")
    ftr_r3Fonts.set(qn("w:ascii"), "Times New Roman")
    ftr_r3Fonts.set(qn("w:hAnsi"), "Times New Roman")
    ftr_r3Fonts.set(qn("w:cs"), "Times New Roman")
    ftr_r3Fonts.set(qn("w:eastAsia"), "Times New Roman")
    ftr_r3Pr.append(ftr_r3Fonts)
    ftr_r3Sz = OxmlElement("w:sz")
    ftr_r3Sz.set(qn("w:val"), "16")
    ftr_r3Pr.append(ftr_r3Sz)
    ftr_r3B = OxmlElement("w:b")
    ftr_r3Pr.append(ftr_r3B)
    ftr_r3.append(ftr_r3Pr)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    fld.set(qn("w:fldLock"), "0")
    ftr_r3.append(fld)
    ftr_p.append(ftr_r3)

    section.footer._element.append(ftr_p)


def _setup_ijirt_header_footer(doc: Document) -> None:
    """Add IJIRT header/footer to ALL sections with independent parts."""
    for i, section in enumerate(doc.sections):
        _create_independent_header_footer(section, is_first_section=(i == 0))


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
        # IJIRT section: centered, uppercase, 10pt plain
        paragraph = _add_centered(doc, text.upper(), size=10, bold=False, space_after=6)
        paragraph.paragraph_format.space_before = Pt(8)
        paragraph.paragraph_format.keep_with_next = True
    else:
        # IJIRT subsection: left, italic, 10pt
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


def _set_cell_shading(cell, color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tc_pr.append(shd)


def _set_row_cant_split(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    tr_pr.append(cant_split)


def _set_header_row_repeat(table) -> None:
    tbl_pr = table._tbl.tblPr
    tbl_header = OxmlElement("w:tblHeader")
    tbl_pr.append(tbl_header)


def _add_table(doc, caption: str, rows: list[list[str]], col_widths: list[float] | None = None) -> None:
    """Add a table with IJIRT formatting: caption above, 8pt body, bold header, grey header fill, full grid."""
    # Caption above table (centred, bold, uppercase, 9pt)
    caption_paragraph = _add_centered(doc, caption.upper(), size=9, bold=True, space_after=2)
    caption_paragraph.paragraph_format.keep_with_next = True

    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    _set_table_borders(table)
    _set_header_row_repeat(table)

    if col_widths:
        # Override the table grid columns (w:tblGrid/w:gridCol) to the exact widths
        tbl = table._tbl
        grid = tbl.find(qn("w:tblGrid"))
        if grid is not None:
            for gc in list(grid.findall(qn("w:gridCol"))):
                grid.remove(gc)
            for w_in in col_widths:
                gc = OxmlElement("w:gridCol")
                gc.set(qn("w:w"), str(int(w_in * 1440)))
                grid.append(gc)
        # Also set tcW on all cells to prevent wrapping issues
        twips_per_inch = 1440
        for row in table.rows:
            for i, w_in in enumerate(col_widths):
                if i < len(row.cells):
                    cell = row.cells[i]
                    tc_pr = cell._tc.get_or_add_tcPr()
                    tcW = tc_pr.find(qn("w:tcW"))
                    if tcW is None:
                        tcW = OxmlElement("w:tcW")
                        tc_pr.append(tcW)
                    tcW.set(qn("w:w"), str(int(w_in * twips_per_inch)))
                    tcW.set(qn("w:type"), "dxa")
        # Disable text wrapping in cells
        for row in table.rows:
            for cell in row.cells:
                tc_pr = cell._tc.get_or_add_tcPr()
                no_wrap = tc_pr.find(qn("w:noWrap"))
                if no_wrap is None:
                    no_wrap = OxmlElement("w:noWrap")
                    tc_pr.append(no_wrap)

    for row_idx, row in enumerate(rows):
        for col_idx, value in enumerate(row):
            cell = table.cell(row_idx, col_idx)
            cell.text = ""
            paragraph = cell.paragraphs[0]
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.line_spacing = 1.0
            _add_inline(paragraph, value, size=8, bold=(row_idx == 0))
            if row_idx == 0:
                _set_cell_shading(cell, "E8E8E8")
        # Prevent row splitting across pages
        _set_row_cant_split(table.rows[row_idx])

    # Small gap after table
    gap = doc.add_paragraph()
    gap.paragraph_format.space_after = Pt(2)
    gap.paragraph_format.space_before = Pt(0)


def _add_image_inline(doc, caption: str, image_path: Path) -> None:
    """Insert figure at column width (3.0 in) inline in two-column flow, caption below."""
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_before = Pt(6)
    para.paragraph_format.space_after = Pt(0)
    run = para.add_run()
    run.add_picture(str(image_path), width=Inches(COLUMN_WIDTH_IN))

    caption_para = _add_centered(doc, caption, size=8, italic=False, space_after=8)
    caption_para.paragraph_format.keep_with_next = True
    caption_para.paragraph_format.keep_together = True


def _add_equation(doc, equation: str) -> None:
    """Equation rendered as a single paragraph with centered equation and right-aligned number."""
    match = re.match(r"^(.*?)(\(\d+\))$", equation.strip())
    eq_text = match.group(1).strip() if match else equation
    number = match.group(2) if match else ""
    # Abbreviate for column width
    eq_text = eq_text.replace("T_route", "T_route").replace("T_token", "T_tok").replace("T_HMAC", "T_HMAC").replace("T_AES", "T_AES").replace("T_serialize", "T_ser")
    
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = para.paragraph_format
    pf.space_before = Pt(4)
    pf.space_after = Pt(4)
    pf.line_spacing = 1.0
    # Add a right tab stop at 3.0in for the equation number
    tab_stops = para.paragraph_format.tab_stops
    tab_stops.add_tab_stop(Inches(3.0), alignment=WD_ALIGN_PARAGRAPH.RIGHT)
    
    # Equation text
    run = para.add_run(eq_text)
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(8)
    run.italic = True
    
    if number:
        # Tab to the right position for equation number
        run_tab = para.add_run("\t")
        run_tab.font.name = "Times New Roman"
        run_tab.font.size = Pt(8)
        run_num = para.add_run(number)
        run_num.font.name = "Times New Roman"
        run_num._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        run_num.font.size = Pt(8)


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
    lines = md.splitlines()
    blocks: list[tuple[str, object]] = []
    paragraph: list[str] = []
    table: list[str] = []
    in_references = False
    ref_buffer: list[str] = []

    def flush_paragraph():
        if paragraph:
            blocks.append(("paragraph", " ".join(paragraph).strip()))
            paragraph.clear()

    def flush_table():
        if table:
            blocks.append(("table", _parse_rows("\n".join(table))))
            table.clear()

    def flush_references():
        nonlocal ref_buffer
        if ref_buffer:
            blocks.append(("references", ref_buffer.copy()))
            ref_buffer.clear()

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## REFERENCES"):
            flush_paragraph()
            flush_table()
            in_references = True
            blocks.append(("heading2", "REFERENCES"))
            continue
        if in_references:
            if stripped.startswith("## "):
                flush_references()
                in_references = False
                blocks.append(("heading2", stripped[3:].strip()))
                continue
            if stripped.startswith("["):
                ref_buffer.append(stripped)
                continue
            if stripped and not stripped.startswith("["):
                flush_references()
                in_references = False
        if stripped.startswith("|"):
            flush_paragraph()
            table.append(stripped)
            continue
        if stripped == "<!-- COLUMN_BREAK -->":
            flush_paragraph()
            flush_table()
            blocks.append(("column_break", None))
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
    flush_references()
    return blocks


def build() -> None:
    front, body = _parse_frontmatter(MANUSCRIPT.read_text(encoding="utf-8"))
    # Create fresh document to avoid base template corruption
    doc = Document()

    # Set default style font
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(10)
    style.paragraph_format.space_after = Pt(4)
    style.paragraph_format.line_spacing = 1.0
    style.paragraph_format.first_line_indent = Inches(0.18)

    # Exactly two sections: one-col title/abstract, continuous break to two-col body
    _style_section(doc.sections[0], count=1, start_type=None)

    # Title block
    _add_centered(doc, front["title"], size=20, bold=False, space_after=8)
    _add_centered(doc, front["authors"], size=11, bold=False, space_after=4)
    _add_centered(doc, front["affiliations"], size=11, italic=True, space_after=10)

    # Abstract
    abstract = doc.add_paragraph()
    abstract.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    abstract.paragraph_format.space_after = Pt(6)
    abstract.paragraph_format.line_spacing = 1.0
    _add_run(abstract, "Abstract—", size=9, bold=True, italic=True)
    _add_inline(abstract, front["abstract"], size=9)

    # Index Terms
    index = doc.add_paragraph()
    index.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    index.paragraph_format.space_after = Pt(6)
    index.paragraph_format.line_spacing = 1.0
    _add_run(index, "Index Terms—", size=9, bold=True, italic=True)
    _add_inline(index, front["index_terms"], size=9)

    # Two-column body
    body_section = doc.add_section(WD_SECTION.CONTINUOUS)
    _style_section(body_section, count=2)

    # Add IJIRT header/footer to all sections
    _setup_ijirt_header_footer(doc)

    # Column widths for the six tables (sum = 3.0 in), keyed by Roman numeral
    TABLE_WIDTHS = {
        "I": [0.60, 1.20, 1.20],      # Requirement, Impl. mechanism, Evidence
        "II": [0.75, 1.25, 1.00],     # Service, Responsibilities, Owned data
        "III": [1.00, 1.10, 0.90],    # Control, Purpose, Validation
        "IV": [1.25, 1.05, 0.70],     # Evaluation item, Outcome, Context
        "V": [0.60, 1.20, 1.20],      # Aspect, Related approaches, Proposed prototype
        "VI": [0.65, 1.35, 1.00],     # Area, Endpoint, Purpose
    }

    table_counter = 0

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
            table_counter += 1
            roman = ["I", "II", "III", "IV", "V", "VI"][table_counter - 1]
            caption = f"TABLE {roman}:"
            col_w = TABLE_WIDTHS.get(roman, None)
            _add_table(doc, caption, rows, col_widths=col_w)
        elif kind == "image":
            caption, image_path = payload
            _add_image_inline(doc, caption, image_path)
        elif kind == "column_break":
            # Force a column break in two-column layout
            brk = doc.add_paragraph()
            run = brk.add_run()
            brk_elem = OxmlElement("w:br")
            brk_elem.set(qn("w:type"), "column")
            run._element.append(brk_elem)
            brk.paragraph_format.space_before = Pt(0)
            brk.paragraph_format.space_after = Pt(0)
        elif kind == "equation":
            _add_equation(doc, payload)
        elif kind == "references":
            # IJIRT style: 9pt, hanging indent 0.25in, no extra space between entries
            for ref in payload:
                para = doc.add_paragraph()
                para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                pf = para.paragraph_format
                pf.space_before = Pt(0)
                pf.space_after = Pt(0)
                pf.line_spacing = 1.0
                pf.first_line_indent = Inches(-0.25)
                pf.left_indent = Inches(0.25)
                _add_inline(para, ref, size=9)

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