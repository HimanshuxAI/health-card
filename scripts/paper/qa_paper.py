"""Quality checks for the generated IJIRT DOCX."""
from __future__ import annotations

import json
import re
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "IJIRT_ABHA_Health_Card_Paper.docx"
REFERENCES = ROOT / "docs" / "paper" / "references.json"


def _sections_info(doc: Document) -> list[dict]:
    result = []
    for section in doc.sections:
        cols = section._sectPr.find(qn("w:cols"))
        result.append(
            {
                "columns": int(cols.get(qn("w:num"), "1")) if cols is not None else 1,
                "left_margin_inches": round(section.left_margin.inches, 2),
                "right_margin_inches": round(section.right_margin.inches, 2),
                "top_margin_inches": round(section.top_margin.inches, 2),
                "bottom_margin_inches": round(section.bottom_margin.inches, 2),
            }
        )
    return result


def _all_text(doc: Document) -> str:
    parts = [paragraph.text for paragraph in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return "\n".join(parts)


def check() -> dict:
    doc = Document(str(OUTPUT))
    text = _all_text(doc)
    references = json.loads(REFERENCES.read_text())["references"]
    missing_citations = [r["id"] for r in references if f"[{r['id']}]" not in text]

    required_headings = [
        "I. INTRODUCTION",
        "II. BACKGROUND AND RELATED WORK",
        "III. SYSTEM DESIGN",
        "IV. IMPLEMENTATION",
        "V. EXPERIMENTAL EVALUATION",
        "VI. DISCUSSION",
        "VII. CONCLUSION",
        "APPENDIX",
        "ACKNOWLEDGMENT",
        "REFERENCES",
    ]
    missing_headings = [heading for heading in required_headings if heading not in text]

    table_titles = re.findall(r"Table\s+([IVX]+)\.", text)
    expected_tables = ["I", "II", "III", "IV", "V", "VI"]
    missing_table_titles = [table for table in expected_tables if table not in table_titles]

    forbidden = [
        "production ready",
        "clinically proven",
        "reduces mortality",
        "guaranteed real-time",
        "guaranteed alert delivery",
        "real ABDM integration",
        "real NHCX integration",
        "offline NFC implemented",
        "NFC hardware implemented",
        "approved by regulator",
    ]
    detected_forbidden = [phrase for phrase in forbidden if phrase.lower() in text.lower()]

    body = text.split("I. INTRODUCTION", 1)[0]
    abstract_only = text.split("Abstract—", 1)[1].split("Index Terms—", 1)[0]
    abstract_word_count = len(re.findall(r"\b[\w’-]+\b", abstract_only))
    body_word_count = len(re.findall(r"\b[\w’-]+\b", text))
    sections_info = _sections_info(doc)
    images = len(doc.inline_shapes)
    tables = len(doc.tables)

    placeholder_count = text.count("Author One")
    unresolved_tokens = re.findall(r"\b(TBD|TODO|FIXME|XXX)\b", text, re.I)

    report = {
        "file": str(OUTPUT),
        "sections": sections_info,
        "images": images,
        "tables": tables,
        "references": len(references),
        "missing_citations": missing_citations,
        "missing_headings": missing_headings,
        "table_titles_present": table_titles,
        "missing_table_titles": missing_table_titles,
        "abstract_word_count": abstract_word_count,
        "total_word_count": body_word_count,
        "intentional_author_placeholders": placeholder_count,
        "unresolved_tokens": unresolved_tokens,
        "detected_forbidden_phrases": detected_forbidden,
        "compressed_archive": True,
    }

    passed = all(
        [
            not missing_citations,
            not missing_headings,
            not missing_table_titles,
            not detected_forbidden,
            not unresolved_tokens,
            images >= 3,
            tables >= 6,
            abstract_word_count >= 150,
        ]
    )
    report["passed"] = passed
    destination = ROOT / "docs" / "paper" / "qa_report.json"
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    report = check()
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)
