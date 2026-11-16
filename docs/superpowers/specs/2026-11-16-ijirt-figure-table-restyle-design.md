# IJIRT Figure and Table Restyle — Design

**Date:** 2026-11-16
**Status:** Approved by user (route: "Restyle DOCX properly", table captions: "Match NexTask LaTeX")
**Scope:** Visual/typographic rebuild of figures, tables, pagination furniture, and PDF export for `IJIRT_ABHA_Health_Card_Paper.docx`.

## 1. Problem (measured)

Inspection of the exported PDF (`IJIRT_ABHA_Health_Card_Paper.pdf`, 11 pages) showed:

| Defect | Measurement | Cause |
|---|---|---|
| Figure text unreadable (~5 pt) | 2400 px canvas, 24 px glyphs, inserted at 6.25 in | Font size chosen in canvas pixels without print-scale conversion |
| Large blank regions (page 3 half empty, page 5 dead zone) | 8 document sections | Every figure forced a 1-column continuous section break; the section could not fit in the remaining column space and was pushed to the next page |
| Tables unreadable | 3 x 2.17 in = 6.5 in built inside a 3.0 in column | Table width ignored the two-column measure; Word/LibreOffice scaled the whole table down |
| No page numbers or journal furniture | Empty header/footer in all 8 sections | Header/footer never populated |
| Rebuild blocked | `Downloads/ijirt_paperformat.docx` no longer exists | Build script referenced an absolute path outside the repository |

The design spec approved on 2026-11-15 already required "figures legible at column width" and "tables without unnecessary outer borders"; the implementation violated both.

## 2. Reference format

`Downloads/NexTask1/paper/NexTask_IJIRT.tex` is the user-supplied IJIRT reference (same LaTeX preamble the user used for another IJIRT paper):

- `twocolumn`, US Letter, 1 in margins, `\columnsep 0.5 in` → **column measure = 3.0 in**
- 10 pt body, Times clone (`mathptmx`), sans-serif running head
- Figures: `width=\linewidth` (column width), centred, caption **below**, centred 9 pt, `Fig. n:` style
- Tables: caption **above**, centred bold uppercase `TABLE I: ...`, 9 pt body, full grid rules, `\hline` header rule
- Running head: right-aligned journal/ISSN line; footer: paper id, journal name, page number

## 3. Design

### 3.1 Figures

- Source of truth: `scripts/paper/generate_figures.py`, regenerated at 300 dpi.
- Canvas: 900 px wide = 3.0 in printed. Conversion rule `pt = px * 0.24` at 300 dpi.
- Type scale: 40 px (9.6 pt) section labels, 36 px (8.6 pt) box titles, 32 px (7.7 pt) body — minimum 7.5 pt in print.
- Composition: vertical stacks only (column-width constraint). No bullet walls, no decorative titles inside the frame (the caption carries the title), no empty margins.
- Grayscale, Arial (sans) to match the reference's sans running head, black on white.
- Fig. 1 architecture: frontends → NGINX gateway → five service rows with database chips → dashed local-simulation boundary containing the simulated ABDM and NHCX gateways.
- Fig. 2 emergency flow: five-step vertical chain (card/token → scan → lookup → HMAC check → AES-GCM decrypt) → five-field profile box → dashed optional-SOS branch → four numbered control points.
- Fig. 3 claim flow: five-step vertical chain (clinical event → FHIR mapping → care context → bill → Claim) → four state chips with permitted transitions → simulated-exchange note.
- Insertion: inline in the two-column flow at 3.0 in, caption below. **No section breaks around figures.**

### 3.2 Tables

- All six tables are rebuilt at the 3.0 in column measure with explicit per-table column widths (ratios chosen per content, never auto-fit).
- Caption above the table, centred, bold, uppercase, `TABLE I: ...` style.
- Body 8 pt, header row bold, light-grey header fill, 0.5 pt grid rules on all edges (matches the reference's `\hline` style).
- Header row repeats on page breaks (`tblHeader`); rows do not split (`cantSplit`); caption is kept with the table (`keep_with_next`).
- Cell wording trimmed to short noun phrases so that no cell exceeds three short lines at 3.0 in.

### 3.3 Page furniture and pagination

- Header (right): `© May 2020 | IJIRT | Volume 6 Issue 12 | ISSN: 2349-6002`, 9 pt sans.
- Footer: left `IJIRT 140001` (replace with the real submission id), centre `INTERNATIONAL JOURNAL OF INNOVATIVE RESEARCH IN TECHNOLOGY`, right `PAGE` field.
- Exactly two sections remain: one-column title/abstract block, continuous break into the two-column body. All figures and tables live inside the two-column body, so no section-induced whitespace can occur.
- Equation table (1) stays inline; it is a layout device, not a data table.

### 3.4 Build reproducibility

- `docs/paper/ijirt_base.docx` is a committed copy of the current styled document, used as the build base (it preserves the template's styles, fonts, and numbering after the body is cleared).
- `scripts/paper/build_docx.py` resolves the base from: `IJIRT_BASE_DOCX` env var → `docs/paper/ijirt_base.docx` → the original `Downloads/ijirt_paperformat.docx` if it is present.
- PDF export: LibreOffice headless (`/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf`).

## 4. Verification

1. `scripts/paper/qa_paper.py` passes: required headings, 25/25 citations, 6 tables, 3 figures, no unresolved tokens, no forbidden claims.
2. Every table measures 3.0 in wide; every figure is 3.0 in wide; document has 2 sections.
3. PDF exported and every page rendered to PNG and visually inspected: no blank half-pages, no clipped tables, no text below 7 pt, captions attached to their objects.
4. Page count target: 8–10 pages (single-column estimate was 14; two-column layout compresses it).
5. No change to claims, measurements, citations, or disclosures.

## 5. Out of scope

- No new experiments, measurements, or citations.
- No change to manuscript prose except caption wording and table-cell trimming.
- No LaTeX port (route explicitly declined in favour of the DOCX rebuild).
