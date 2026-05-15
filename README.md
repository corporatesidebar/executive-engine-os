# Executive Engine OS — V35150B Backend Fix

Backend-only package for **V35150B — Selective /run Response Quality Contract Patch**.

## Scope

This package restores backend version consistency and verification endpoints only.

Included:
- `backend/main.py`
- `backend/requirements.txt`
- `README.md`
- `test-checklist.md`

Not included:
- frontend files
- Supabase changes
- DB schema changes
- deployment setting changes
- memory features
- V35160 features

## Endpoint Target

Live backend URL:

`https://executive-engine-os.onrender.com`

## Version Target

All backend endpoints report:

`V35150B`

## Restored / Fixed Endpoints

- `GET /`
- `GET /health`
- `GET /debug`
- `GET /test-report`
- `GET /test-report-json`
- `POST /run`

## /run Contract

Every successful `POST /run` response returns exactly:

- `next_move`
- `decision`
- `action_steps`
- `ready_assets`
- `risk`
- `priority`
- `recommended_command`

`action_steps` and `ready_assets` are always arrays. `priority` is always `High`, `Medium`, or `Low`.

## Test Page

Open:

`https://executive-engine-os.onrender.com/test-report`

The page includes:
- Run Tests button
- Copy JSON button
- PASS / FAIL status display
- Raw JSON output

## Deployment Notes

Deploy as backend service only. Do not deploy to the frontend Render service.
