# Design Spec — IJIRT Research Paper for the ABHA Health Card Project

Date: 2026-11-15  
Project: SY1512 — School of Computing, MIT-ADT University  
Deliverable: A submission-ready Microsoft Word manuscript based on `/Users/himanshu/Downloads/ijirt_paperformat.docx`

## 1. Objective

Create an original 8–10 page IJIRT-style empirical engineering paper that presents the implemented ABHA health-card prototype as a reproducible system contribution. The paper must follow the attached IJIRT template, report only evidence obtainable from the local project, distinguish implemented functionality from simulated or future functionality, and avoid unsupported claims of zero plagiarism, production readiness, clinical validation, or national-gateway integration.

## 2. Confirmed Decisions

| Decision | Choice |
|---|---|
| Paper direction | Empirical engineering paper: architecture, implementation, measured evaluation, discussion, and limitations |
| Length | Approximately 8–10 pages in the supplied template |
| Deliverable | Completed `.docx`; no separate editable manuscript is required |
| Template | Preserve the supplied IJIRT layout, typography, section conventions, and reference style |
| Authors | Clear, replaceable project placeholders |
| Evidence | Run the existing tests and reproducible local benchmarks; report exact measured values |
| Integrity | Original synthesis, verified citations, and an internal source-overlap check; no claim of a guaranteed 0% external similarity score |
| ABDM/NHCX | Describe as locally simulated, real-shaped gateways; never claim live national integration |
| Offline/NFC | Treat the original NFC/offline-decryption objective as unimplemented future work, not as a completed result |

## 3. Proposed Title

**An ABHA-Integrated Emergency Health Card Prototype: Secure QR Retrieval, FHIR Interoperability, and Claims Synchronization**

The title deliberately omits “offline-capable” because the completed prototype uses an HMAC-signed QR token resolved by the records service rather than storing the complete encrypted trauma profile on an NFC tag.

## 4. Required Paper Structure

1. **Title, authors, and affiliations** — author placeholders and School of Computing, MIT-ADT University.
2. **Abstract** — original 170–200-word summary with no citations.
3. **Index Terms** — at least four terms in alphabetical order.
4. **I. Introduction** — context, problem, research gap, objectives, and contribution summary.
5. **II. Background and Related Work** — ABHA/ABDM, FHIR, NHCX, emergency health cards, consent, encryption, and a focused comparison with representative approaches.
6. **III. System Design**
   - Requirements and design goals
   - Microservice architecture
   - Identity, consent, and role-based authorization
   - Emergency-profile sealing and QR-token resolution
   - FHIR/ABDM care-context workflow
   - NHCX claim synchronization and state machine
   - SOS notification workflow
7. **IV. Implementation** — frontend, FastAPI services, per-service SQLite ownership, NGINX gateway, data structures, and representative API flows.
8. **V. Experimental Evaluation**
   - Reproducible environment
   - Functional test results
   - Emergency-resolution latency benchmark
   - Tamper and authentication checks
   - Objective-to-evidence traceability
9. **VI. Discussion** — findings, comparison with related work, threats to validity, limitations, and future work.
10. **VII. Conclusion** — concise findings without repeating the abstract.
11. **Appendix** — endpoint map, test inventory, and reproduction instructions; placed before the acknowledgment as specified by the template.
12. **Acknowledgment** — project/institution acknowledgment without invented funding or sponsorship.
13. **References** — verified sources in the template’s numbered square-bracket style.

## 5. Visual and Tabular Evidence

- **Fig. 1:** System architecture showing the Next.js frontend, NGINX gateway, five FastAPI services, and database ownership.
- **Fig. 2:** Emergency QR retrieval and SOS sequence.
- **Fig. 3:** Clinical-record-to-FHIR-to-NHCX claim workflow.
- **Table I:** Requirements-to-implementation-to-evidence traceability matrix.
- **Table II:** Service responsibilities and data ownership.
- **Table III:** Security controls and their validation.
- **Table IV:** Measured evaluation results.
- **Table V:** Representative comparison with related approaches.

All figures and tables must correspond to actual project behavior. No user-study, clinical, production-scale, or field-deployment results may be invented.

## 6. Measurement Protocol

1. Run the existing service test suites and record the exact test count and result.
2. Run the existing 16-step end-to-end workflow when the local services can be started safely; record each successful stage or a precise failure.
3. Benchmark emergency-token resolution repeatedly against the local records service or a faithful local test harness.
4. Report the sample count, minimum, maximum, mean, median, and p95 server-side resolution time.
5. Record processor, operating system, Python/runtime version, service mode, and any material benchmarking constraints.
6. Validate AES-GCM sealing/unsealing, ciphertext/HMAC tamper rejection, JWT authentication, role authorization, inactive-token behavior, consent behavior, FHIR resource shape, NHCX state transitions, and SOS workflow behavior.
7. Distinguish unit/integration results from end-to-end and benchmark results in the tables and prose.

Local timing must be described as local timing and must not be generalized to production-network or field performance.

## 7. Research-Integrity Rules

- Write all prose from scratch and avoid sentence-pattern imitation from sources.
- Cite factual claims using verified references in consecutive square brackets.
- Include complete bibliographic details; do not use “et al.” unless a source has six or more authors.
- Use stable DOI or official URLs where appropriate.
- Do not cite sources in the abstract.
- Do not copy template instruction text into the manuscript except required labels or conventions.
- Perform an internal overlap scan against the supplied synopsis, extracted source text, and cited web material.
- Report that external plagiarism tools may use different databases and similarity thresholds; do not promise a guaranteed score of zero.

## 8. Scope Boundaries and Required Disclosures

The manuscript must not claim:

- physical NFC/NTAG216 support;
- complete zero-connectivity operation;
- live ABDM or NHCX sandbox connectivity;
- SMS delivery;
- production-grade key management;
- an external security audit;
- clinical validation or improved patient outcomes;
- large-scale performance or multi-node deployment.

The Discussion section must identify these limitations and explain that offline NFC retrieval, managed key rotation, real gateway certification, stronger notification delivery, and a prospective usability/clinical study are future work.

## 9. Word Formatting

Use `/Users/himanshu/Downloads/ijirt_paperformat.docx` as the base document and replace the instructional body with manuscript content.

- Page size: US Letter, 8.5 × 11 inches.
- Margins: 1 inch on all sides.
- Opening section: one column for title, authors, affiliations, abstract, and index terms.
- Body: continuous section break to two columns with the template’s 0.5-inch gutter.
- Title: Times New Roman, 20 pt, centered.
- Authors and affiliations: Times New Roman, 11 pt, centered.
- Abstract and index terms: Times New Roman, 9 pt, justified.
- Body: Times New Roman, 10 pt, justified.
- Section headings: Times New Roman, 10 pt, centered, Roman-numeral hierarchy.
- Subsection headings: lettered hierarchy.
- Figures: centered, grayscale/vector-like, legible at column width; captions below using `Fig. n.`.
- Tables: title above, Roman-numeral labels, no unnecessary outer borders, readable at column width.
- Equations: numbered consecutively, with symbols defined and right-aligned equation numbers where used.
- References: numbered square brackets, complete details, correct punctuation.

## 10. Deliverable and Quality Gates

### Deliverable

`IJIRT_ABHA_Health_Card_Paper.docx` in the project root.

### Quality gates

- The document opens as a valid Office Open XML `.docx`.
- The page count is approximately 8–10 pages.
- The title/abstract section remains one column and the main body is two columns.
- All headings follow the approved Roman-numeral and lettered hierarchy.
- Every numbered citation resolves to one reference, and every reference is cited in the paper.
- Every figure and table is mentioned in the prose.
- All measured values come from an executed test or benchmark and include sufficient context.
- The only unresolved placeholders are the intentionally replaceable author details.
- No unsupported claim of production readiness, clinical validation, true offline operation, or zero plagiarism appears.
- The final file preserves the original template file rather than modifying it in place.
