#!/usr/bin/env python3
"""Build the MIT-ADT B.Tech project report from docs/report/project_report.md."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "report" / "project_report.md"
OUTPUT = ROOT / "deliverables" / "ABHA_Health_Card_Project_Report.docx"


def _frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}, text
    data = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"')
    return data, text[match.end():]


def _add_run(paragraph, text: str, size: float, bold: bool = False, italic: bool = False):
    run = paragraph.add_run(text)
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    return run


def _para(doc, text="", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False, italic=False,
          space_after=6, first_indent=0.25, space_before=0):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.5
    pf.first_line_indent = Inches(first_indent) if first_indent else None
    if text:
        _add_run(p, text, size=size, bold=bold, italic=italic)
    return p


def _heading(doc, text, level):
    text = text.strip()
    if level == 1:
        p = _para(doc, text.upper(), size=18, align=WD_ALIGN_PARAGRAPH.CENTER,
                  bold=True, space_before=24, space_after=12, first_indent=0)
    elif level == 2:
        p = _para(doc, text.upper(), size=12, align=WD_ALIGN_PARAGRAPH.LEFT,
                  bold=True, space_before=12, space_after=6, first_indent=0)
    else:
        p = _para(doc, text, size=12, align=WD_ALIGN_PARAGRAPH.LEFT,
                  bold=True, space_before=8, space_after=4, first_indent=0)
    return p


def _bullet(doc, text):
    p = _para(doc, "", size=12, first_indent=0, space_after=4)
    pf = p.paragraph_format
    pf.left_indent = Inches(0.5)
    pf.first_line_indent = Inches(-0.25)
    _add_run(p, "•  ", size=12, bold=True)
    _add_run(p, text, size=12)
    return p


def _numbered(doc, number, text):
    p = _para(doc, "", size=12, first_indent=0, space_after=4)
    pf = p.paragraph_format
    pf.left_indent = Inches(0.5)
    pf.first_line_indent = Inches(-0.25)
    _add_run(p, f"{number}.  ", size=12, bold=True)
    _add_run(p, text, size=12)
    return p


def _table(doc, rows):
    if not rows:
        return
    cols = len(rows[0])
    table = doc.add_table(rows=len(rows), cols=cols)
    table.style = "Table Grid"
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r_idx, row in enumerate(rows):
        for c_idx, value in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pf = p.paragraph_format
            pf.space_before = Pt(2)
            pf.space_after = Pt(2)
            pf.line_spacing = 1.1
            run = p.add_run(value)
            run.font.name = "Times New Roman"
            run.font.size = Pt(10)
            run.bold = (r_idx == 0)
    # header shading
    for c_idx in range(cols):
        tc_pr = table.rows[0].cells[c_idx]._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), "D9D9D9")
        tc_pr.append(shd)
    _para(doc, "", size=6, space_after=2, first_indent=0)
    return table


def _parse_rows(block):
    rows = []
    for line in block.strip().splitlines():
        if not line.strip().startswith("|"):
            continue
        if set(line.replace("|", "").strip()) <= {"-", " ", ":"}:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append(cells)
    return rows



def _add_image(doc, caption, image_path):
    path = Path(image_path)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        _para(doc, f"[Image not found: {caption}]", size=10, italic=True, first_indent=0)
        return
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = para.paragraph_format
    pf.space_before = Pt(6)
    pf.space_after = Pt(0)
    run = para.add_run()
    run.add_picture(str(path), width=Inches(6.0))
    cap = _para(doc, caption, size=9, align=WD_ALIGN_PARAGRAPH.CENTER,
                bold=True, space_after=8, first_indent=0)
    cap.paragraph_format.keep_with_next = True


def _add_toc_field(doc):
    paragraph = doc.add_paragraph()
    run = paragraph.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = r'TOC \o "1-2" \h \z \u'
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "separate")
    fld_char3 = OxmlElement("w:fldChar")
    fld_char3.set(qn("w:fldCharType"), "end")
    run._element.append(fld_char1)
    run._element.append(instr)
    run._element.append(fld_char2)
    run._element.append(fld_char3)
    return paragraph


def build():
    text = SOURCE.read_text(encoding="utf-8")
    _frontmatter(text)
    body = text.split("---", 2)[2] if text.startswith("---") else text

    doc = Document()

    # Base style
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.first_line_indent = Inches(0.25)

    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.25)
    section.right_margin = Inches(1.0)

    # Footer
    footer_p = section.footer.paragraphs[0]
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer_p.add_run("MITSOC, Department of Computer Science and Engineering 2026  |  Page ")
    run.font.name = "Times New Roman"
    run.font.size = Pt(10)
    # page number field
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    sz = OxmlElement("w:sz"); sz.set(qn("w:val"), "20"); rpr.append(sz)
    r.append(rpr)
    t = OxmlElement("w:t"); t.text = "1"; r.append(t)
    fld.append(r)
    footer_p._element.append(fld)

    lines = body.splitlines()
    i = 0
    paragraph_buffer = []

    def flush_paragraph():
        nonlocal paragraph_buffer
        if paragraph_buffer:
            joined = " ".join(paragraph_buffer).strip()
            if joined:
                if joined.startswith("Table:"):
                    _para(doc, joined, size=10, align=WD_ALIGN_PARAGRAPH.CENTER,
                          bold=True, space_after=2, first_indent=0)
                else:
                    _para(doc, joined, size=12)
            paragraph_buffer = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            i += 1
            continue
        if stripped == "[TOC]":
            flush_paragraph()
            _add_toc_field(doc)
            i += 1
            continue
        if stripped.startswith("![") and stripped.endswith(")"):
            flush_paragraph()
            match = re.match(r"!\[(.*?)\]\((.*?)\)", stripped)
            if match:
                _add_image(doc, match.group(1), match.group(2))
            i += 1
            continue
        if stripped.startswith("|"):
            flush_paragraph()
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            _table(doc, _parse_rows("\n".join(table_lines)))
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            _heading(doc, stripped[2:], 1)
            i += 1
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            _heading(doc, stripped[3:], 2)
            i += 1
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            _heading(doc, stripped[4:], 3)
            i += 1
            continue
        match = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if match:
            flush_paragraph()
            _numbered(doc, int(match.group(1)), match.group(2))
            i += 1
            continue
        if stripped.startswith("- "):
            flush_paragraph()
            _bullet(doc, stripped[2:])
            i += 1
            continue
        paragraph_buffer.append(stripped)
        i += 1
    flush_paragraph()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUTPUT))
    print(f"Built {OUTPUT}")


if __name__ == "__main__":
    build()
