# Submission checklist (official items from Appendix 2)

Deadline: 20 Oct 2026 23:59 Beijing (UTC+8) = 21:29 IST. Channel (per secondary listings; confirm on fintechathon.g-ican.com): email to wangyr@pbcsf.tsinghua.edu.cn with registration form and passport bio pages, plus deliverables.

| # | Official item | File(s) | Status |
|---|---|---|---|
| 01 | Technical documentation: architecture, core algorithm, security design | `docs/05_TECHNICAL_DOCUMENTATION.md`, `docs/04_SYSTEM_ARCHITECTURE.md` (+ PDF export, see below) | VERIFIED COMPLETE (Markdown); PDF export: run `pandoc` or print-to-PDF |
| 02 | Presentation deck, ≤ 10 min | `slides/PRESENTATION_DECK.pptx` via `python scripts/build_slides.py`; `slides/SPEAKER_NOTES.md` | COMPLETE WITH LIMITATIONS — generate and inspect locally; add screenshots |
| 03 | Demo video (optional, ≤ 5 min) | storyboard in `docs/10_DEMO_RUNBOOK.md` | OUTSTANDING (optional) |
| 04 | Source code with README, GitHub link, deployment instructions, test cases | repo root, `README.md`, `tests/` | VERIFIED COMPLETE locally; GitHub URL REQUIRES TEAM ACTION |
| 05 | Security self-assessment: permission tiers, known risks | `docs/06_SECURITY_SELF_ASSESSMENT.md`, `docs/09_KNOWN_RISKS.md` | VERIFIED COMPLETE |
| 06 | Execution evidence: sandbox logs (+ demo video) | `evidence/operation_logs/`, `evidence/test_results/`, `evidence/screenshots/` | COMPLETE WITH LIMITATIONS — logs/tests real; video outstanding |
| — | Eligibility: 2–5 students, overseas institutions, ≥60% non-Chinese nationals, English | registration form | REQUIRES TEAM INFORMATION |
| — | Team name, GitHub URL, licence holder | `LICENSE`, docs headers, email draft | REQUIRES TEAM INFORMATION |

PDF export commands (optional): `pandoc docs/05_TECHNICAL_DOCUMENTATION.md docs/04_SYSTEM_ARCHITECTURE.md -o docs/TECHNICAL_DOCUMENTATION.pdf` (Mermaid blocks render as code unless a Mermaid filter is installed; alternatively open the Markdown in VS Code with a Mermaid preview and print to PDF). Slides to PDF: `soffice --headless --convert-to pdf slides/PRESENTATION_DECK.pptx --outdir slides`.

Final packaging: `cd .. && python3 -m zipfile -c TuitionBridge_FinTechathon2026_Submission.zip tuitionbridge` after removing `.venv`, `*.db`, `__pycache__` (`.gitignore` lists them; `git archive` is cleaner once committed).
