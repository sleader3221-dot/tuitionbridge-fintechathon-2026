# Submission Checklist

## Current package status

**Team:** TuitionBridge FinTech Lab
**Track and topic:** International track, Topic C (Cross-border & Student Finance Assistant)
**Public source repository:** https://github.com/sleader3221-dot/tuitionbridge-fintechathon-2026

| # | Deliverable | Location | Status |
|---|---|---|---|
| 01 | Technical documentation | `docs/05_TECHNICAL_DOCUMENTATION.md`, `docs/04_SYSTEM_ARCHITECTURE.md` | Complete in Markdown; export to PDF only if the organizer requires it. |
| 02 | Presentation, up to 10 minutes | `slides/PRESENTATION_DECK.pptx`, `slides/SPEAKER_NOTES.md` | 14-slide deck generated. Four demo screenshots are embedded; visually inspect it in PowerPoint before submission. |
| 03 | Demo video, optional, up to 5 minutes | Storyboard in `docs/10_DEMO_RUNBOOK.md` | Not recorded. Optional according to the provided checklist; confirm current rules. |
| 04 | Source, README, tests, repository URL | Repository root, `README.md`, `tests/` | Public repository exists. 60 tests passed in the recorded run; see `evidence/test_results/`. |
| 05 | Security self-assessment | `docs/06_SECURITY_SELF_ASSESSMENT.md`, `docs/09_KNOWN_RISKS.md` | Complete. |
| 06 | Execution evidence | `evidence/operation_logs/`, `evidence/test_results/`, `evidence/screenshots/` | Scenario logs, test output, and screenshots are present. Screenshots and deck still need human visual review. |
| — | Team roster and eligibility | Private working template outside this repository | Two-member roster is expected by the user; second member details and organizer eligibility criteria still need confirmation. |
| — | Registration and delivery channel | Official competition website and registration form | Current recipient address and international-track cutoff were not verified from accessible official page text. Confirm with the organizer before sending identity documents. |

## Deadline and delivery checks

A previous working note listed **20 October 2026, 23:59 China Standard Time (20 October 2026, 21:29 India Standard Time)**. China Standard Time is 2 hours 30 minutes ahead of India Standard Time. The current official website displays 2026 competition information, but the accessible page text does not establish the international-track submission deadline or delivery email. Check the current international-track notice or registration confirmation before relying on any date or recipient.

Official site: <https://fintechathon.g-ican.com/>

Do not send passport pages to an address copied from a secondary listing. Verify the recipient through the current official registration flow or directly with the organizer.

## Package contents

The repository contains the source, test results, scenario logs, screenshots, and generated PowerPoint deck. Build a clean archive from the committed revision with `git archive`; this omits ignored local files such as virtual environments and databases. If evidence or slide files are not tracked in the revision being archived, add them only after reviewing the archive contents.
