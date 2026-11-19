#!/usr/bin/env python3
"""Build the Annexure 7 success story DOCX."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "report" / "success_story.md"
OUTPUT = ROOT / "deliverables" / "ABHA_Health_Card_Success_Story.docx"


def _add_run(p, text, size=12, bold=False, italic=False):
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    return run


def _para(doc, text="", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False, italic=False,
          space_after=6, space_before=0, first_indent=0.25):
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
    if level == 1:
        _para(doc, text.upper(), size=16, align=WD_ALIGN_PARAGRAPH.CENTER,
              bold=True, space_before=18, space_after=8, first_indent=0)
    else:
        _para(doc, text, size=12, align=WD_ALIGN_PARAGRAPH.LEFT,
              bold=True, space_before=12, space_after=4, first_indent=0)


def _table(doc, rows):
    if not rows:
        return
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.style = "Table Grid"
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
    _para(doc, "", size=6, space_after=2, first_indent=0)


def _parse_rows(block):
    rows = []
    for line in block.strip().splitlines():
        if not line.strip().startswith("|"):
            continue
        if set(line.replace("|", "").strip()) <= {"-", " ", ":"}:
            continue
        rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def build():
    text = SOURCE.read_text(encoding="utf-8")
    body = text.split("---", 2)[2] if text.startswith("---") else text
    doc = Document()
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

    footer_p = section.footer.paragraphs[0]
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer_p.add_run("MITSOC, Department of Computer Science and Engineering 2026  |  Page ")
    run.font.name = "Times New Roman"
    run.font.size = Pt(10)
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
    buffer = []

    def flush():
        nonlocal buffer
        if buffer:
            joined = " ".join(buffer).strip()
            if joined:
                _para(doc, joined, size=12)
            buffer = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            flush()
            i += 1
            continue
        if stripped.startswith("Table:"):
            flush()
            _para(doc, stripped, size=10, align=WD_ALIGN_PARAGRAPH.CENTER,
                  bold=True, space_after=2, first_indent=0)
            i += 1
            continue
        if stripped.startswith("|"):
            flush()
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            _table(doc, _parse_rows("\n".join(table_lines)))
            continue
        if stripped.startswith("# "):
            flush()
            _heading(doc, stripped[2:], 1)
            i += 1
            continue
        if stripped.startswith("## "):
            flush()
            _heading(doc, stripped[3:], 2)
            i += 1
            continue
        buffer.append(stripped)
        i += 1
    flush()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUTPUT))
    print(f"Built {OUTPUT}")


if __name__ == "__main__":
    build()
