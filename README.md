# Executive Engine OS — V35160B Backend Response Comprehension Fix

Backend-only package.

## Purpose
Fix `/run` intelligence and readability without changing frontend, layout, navigation, database, Supabase, Claude routing, or deployment settings.

## What changed
- Stronger auto-intent filter.
- Proposal intent wins over meeting/revenue/execution when the command contains proposal, dealership, SEO, Google Ads, CPA, or auto-loan language.
- Guard prevents proposal requests from returning Costa Rica, relocation, residency, lifestyle, or job-search content.
- More concise output fields for frontend readability.
- Preserves required `/run` contract.
- Preserves `/test-report` browser page with Run Tests and Copy JSON.

## Files
- `backend/main.py`
- `backend/requirements.txt`
- `README.md`
- `test-checklist.md`

## Required test prompt
`Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.`

Expected: dealership proposal output only. No Costa Rica or relocation content.
