"""N-gram overlap scan against the supplied synopsis and IJIRT template."""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import pymupdf
from docx import Document

ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT = ROOT / "docs" / "paper" / "manuscript.md"
SYNOPSIS_PDF = ROOT / "SY1512.pdf"
TEMPLATE_DOCX = Path("/Users/himanshu/Downloads/ijirt_paperformat.docx")


def normalize(text: str) -> list[str]:
    text = text.lower().replace("’", "'")
    tokens = re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)*", text)
    return tokens


def shingles(tokens: list[str], size: int = 7) -> set[tuple[str, ...]]:
    return {tuple(tokens[i : i + size]) for i in range(len(tokens) - size + 1)}


def load_sources() -> dict[str, str]:
    sources = {}
    with pymupdf.open(SYNOPSIS_PDF) as document:
        sources["project_synopsis"] = "\n".join(page.get_text("text") for page in document)
    doc = Document(str(TEMPLATE_DOCX))
    sources["ijirt_template"] = "\n".join(p.text for p in doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                sources["ijirt_template"] += "\n" + cell.text
    return sources


def scan(size: int = 7) -> dict:
    manuscript_tokens = normalize(MANUSCRIPT.read_text(encoding="utf-8"))
    manuscript_shingles = shingles(manuscript_tokens, size)
    report = {"ngram_size": size, "manuscript_shingles": len(manuscript_shingles), "sources": {}}
    for name, raw in load_sources().items():
        source_shingles = shingles(normalize(raw), size)
        overlap = manuscript_shingles & source_shingles
        report["sources"][name] = {
            "source_shingles": len(source_shingles),
            "overlap_count": len(overlap),
            "overlap_percent_of_manuscript": round(100 * len(overlap) / len(manuscript_shingles), 2) if manuscript_shingles else 0,
            "examples": [" ".join(item) for item in sorted(overlap)[:5]],
        }
    report["max_overlap_percent_of_manuscript"] = max(
        source["overlap_percent_of_manuscript"] for source in report["sources"].values()
    )
    report["passed"] = report["max_overlap_percent_of_manuscript"] <= 2.0
    destination = ROOT / "docs" / "paper" / "originality_report.json"
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(scan(), indent=2))
