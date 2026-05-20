# Executive Engine OS — V36200 Command System

## Decision
This build renames the core work unit from generic chats/tasks to **Commands** and preserves the locked `/run` output contract.

## Included Files
```text
frontend/index.html
backend/main.py
backend/requirements.txt
README.md
```

## What Changed
- Core unit name: **Command**
- Primary button: **Run Command**
- Sidebar: **Active Commands**
- Placeholder: **What do we need to accomplish?**
- Backend `/run` produces required executive fields:
  - next_move
  - decision
  - action_steps
  - ready_assets
  - risk
  - priority
  - recommended_command
- OpenAI is used when `OPENAI_API_KEY` exists.
- Local fallback engine prevents weak/empty output when OpenAI fails.

## Deploy
### Backend Render
Root directory: `backend`
Start command:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```
Environment:
```text
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
```

### Frontend Render Static Site
Root directory: `frontend`
Publish directory: `.`

## Test Checklist
1. GET `/health` returns status ok.
2. POST `/run` returns all required fields.
3. Frontend loads.
4. Run Command posts to `https://executive-engine-os.onrender.com/run`.
5. Output displays in locked order.
6. Ready Assets contain actual copy/assets, not generic advice.

## Known Limitation
Frontend API URL is hardcoded to production backend: `https://executive-engine-os.onrender.com`.
