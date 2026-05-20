# V36250 — PDF Download Fix

Frontend-only update.

## Fixed
- Header Download button now exports a PDF brief instead of JSON.
- PDF includes: generated date, active category, executive summary, Do Now items, top priorities, and current command thread.
- No backend, layout, navigation, or API changes.

## Test
- Static HTML syntax check passed.
- Verified the JSON download handler was removed.
- Verified PDF download filename: `executive-engine-command-brief.pdf`.
