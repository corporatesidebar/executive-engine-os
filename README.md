# Executive Engine OS — V35160 Backend Response Intelligence Fix

Backend-only package.

## Purpose
Fix `/run` response intelligence without changing frontend, database, Supabase, navigation, layout, deployment settings, or provider routing.

## What changed
- Preserves `POST /run`.
- Preserves required output contract:
  - `next_move`
  - `decision`
  - `action_steps`
  - `ready_assets`
  - `risk`
  - `priority`
  - `recommended_command`
  - `provider_used`
  - `status`
- Adds deterministic intent routing for:
  - proposal
  - meeting
  - decision
  - revenue
  - follow_up
  - strategy
  - execution
  - risk
  - general
- Adds proposal guard so dealership / SEO / Google Ads / CPA prompts cannot return relocation or unrelated output.
- Preserves `/`, `/health`, `/debug`, `/test-report`, `/test-report-json`.
- Preserves `/test-report` browser tools: Run Tests and Copy JSON.

## Files
```text
backend/main.py
backend/requirements.txt
README.md
test-checklist.md
```

## Do not deploy to frontend
Deploy this package to the backend Render service only.
