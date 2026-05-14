# Executive Engine OS — V35150A Test Page Restore

Backend-only package to restore the useful `/test-report` browser test console.

## Scope
- Restores `/test-report` UI only.
- Preserves `/run` output contract.
- Does not include frontend files.
- Does not include DB, Supabase, Claude, OpenAI routing, memory/actions, or V35160 features.

## Required Contract
- `next_move`
- `decision`
- `action_steps`
- `ready_assets`
- `risk`
- `priority`
- `recommended_command`

## Endpoints
- `GET /`
- `GET /health`
- `GET /debug`
- `POST /run`
- `GET /test-report`
- `GET /test-report-json`

## Deploy
Deploy the `backend/` folder only to the existing backend Render service.
