# Executive Engine OS — V35150 Real Output Contract

Backend-only build.

## Scope

- Preserves `POST /run`.
- Preserves `GET /health`.
- Does not include frontend files.
- Does not touch DB, Supabase, Claude, memory, or deployment settings.
- Enforces a stable `/run` JSON response contract.

## Required `/run` response contract

```json
{
  "next_move": "",
  "decision": "",
  "action_steps": [],
  "ready_assets": [],
  "risk": "",
  "priority": "High | Medium | Low",
  "recommended_command": ""
}
```

## Files

```text
backend/main.py
backend/requirements.txt
README.md
test-checklist.md
```

## Deploy note

Deploy backend only. Do not upload or modify frontend files.
