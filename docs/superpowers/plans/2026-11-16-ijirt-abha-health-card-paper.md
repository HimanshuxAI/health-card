# IJIRT ABHA Health Card Paper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. The user has already requested immediate content delivery; execute inline without further questions. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a completed 8–10 page original IJIRT DOCX paper on the implemented ABHA health-card prototype.

**Architecture:** Collect reproducible evidence from the repository, draft a manuscript with verified citations and explicit simulation limitations, generate architecture/workflow figures, and assemble the final DOCX from the supplied template while preserving its one-column front matter and two-column body.

**Tech Stack:** Python 3.13, pytest, FastAPI/TestClient, SQLAlchemy, PyCryptodome, Pillow, python-docx, markdown-it-py, JSON, and the supplied IJIRT Word template.

---

## File Structure

- `requirements-paper.txt` — paper-generation dependencies.
- `scripts/paper/evidence.py` — environment capture, statistics, and evidence persistence.
- `scripts/paper/benchmark_emergency.py` — isolated emergency-resolution benchmark.
- `scripts/paper/run_live_e2e.sh` — live service and 16-step workflow runner.
- `docs/paper/evidence.json` — machine-readable measured evidence.
- `docs/paper/e2e.txt` — live end-to-end output.
- `docs/paper/references.json` — 25 verified citation records.
- `docs/paper/manuscript.md` — canonical paper text.
- `scripts/paper/generate_figures.py` — architecture and workflow PNGs.
- `docs/paper/figures/` — generated grayscale figures.
- `scripts/paper/build_docx.py` — template-preserving DOCX builder.
- `scripts/paper/qa_paper.py` — format/content/quality checks.
- `scripts/paper/originality_check.py` — n-gram overlap scan against provided sources.
- `IJIRT_ABHA_Health_Card_Paper.docx` — final manuscript.

## Task 1 — Paper Tooling

- [x] Create and install `requirements-paper.txt`.
- [x] Capture system/runtime environment.
- [x] Verify baseline tests.

## Task 2 — Evidence Collection

- [x] Implement statistics helpers.
- [x] Benchmark emergency resolution on an isolated temporary database.
- [x] Record unit/integration results and benchmark statistics in `evidence.json`.
- [x] Run the 16-step live end-to-end workflow.
- [x] Record exact outputs and local context.

## Task 3 — Verified Bibliography

- [x] Encode the 25-reference dossier with authors, venue, year, volume/issue/pages, DOI, and access/version data.
- [x] Validate uniqueness and required fields.
- [x] Map every reference to the section where it will be cited.

## Task 4 — Manuscript Draft

- [x] Draft front matter, abstract, and index terms.
- [x] Draft I. Introduction through VII. Conclusion.
- [x] Add all five tables and all referenced figures.
- [x] Add appendix, acknowledgment, and complete reference list.
- [x] Enforce unsupported-claim boundaries and simulation disclosures.

## Task 5 — Figures and DOCX

- [x] Generate three grayscale figures.
- [x] Build DOCX from the attached IJIRT template.
- [x] Preserve one-column front matter and continuous two-column body.
- [x] Apply IJIRT fonts, heading hierarchy, captions, and references.

## Task 6 — Quality Review

- [x] Validate DOCX structure, sections, fonts, margins, citations, figures, tables, and word count.
- [x] Run n-gram source-overlap scan.
- [x] Produce a completion report with evidence, placeholders, and limitations.
- [x] Commit the paper deliverables.
