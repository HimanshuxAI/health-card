# Paper Completion Report

## Deliverable

- `IJIRT_ABHA_Health_Card_Paper.docx`

## Verified evidence

- **19/19 service tests passed.**
- **16/16 live end-to-end workflow steps passed.**
- **1,000-request local emergency-resolution benchmark passed**, with:
  - median wall time: **0.644 ms**
  - mean wall time: **0.661 ms**
  - 95th-percentile wall time: **0.743 ms**
  - minimum/maximum wall time: **0.612/1.908 ms**
  - all responses HTTP 200
- The benchmark is local in-process timing and excludes QR acquisition, TLS, network transit, and browser rendering.
- The service’s integer timer reported a median of 0 ms because many sub-millisecond calls rounded down.

## Integrity checks

- **25/25 references are cited in the manuscript.**
- **0 unresolved citations.**
- All required section headings and all six labeled tables are present.
- Three generated figures are embedded.
- The DOCX archive passes integrity validation.
- Estimated page count is approximately **8–10 pages** in the two-column IJIRT layout; a single-column PDF conversion rendered **14 pages**, consistent with about 7–8 pages when split into two columns.
- A 7-word n-gram overlap scan against the supplied synopsis and IJIRT template reported:
  - **0.02% overlap** with the project synopsis.
  - **0.00% overlap** with the IJIRT template.
- This is an internal overlap scan, not a claim of any external plagiarism-checker score.

## Intentional placeholders

- `Author One`
- `Author Two`
- `Author Three`

These are clearly replaceable author placeholders; they should be updated with real author names and the correct affiliation/email ordering before submission.

## Important disclosures

- ABDM and NHCX are locally simulated, real-shaped services, not live national-gateway integrations.
- The prototype does not implement physical NFC/NTAG216 storage or complete offline operation.
- It uses WebSocket and optional SMTP rather than SMS.
- It does not claim production key management, external security audit, clinical validation, or improved patient outcomes.
- Future work includes offline NFC retrieval, live ABDM/NHCX conformance testing, break-glass governance, managed key rotation, degraded-network testing, and clinician usability studies.

## Next step for the team

Replace the author placeholders in the DOCX title block, then review the measured benchmark wording and disclosures before submission.
