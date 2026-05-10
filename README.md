# Executive Engine OS — V36330 Stable Merge Recovery

## Version
V36330 — Stable Merge Recovery

## Included Files

```text
/frontend/index.html
/backend/main.py
/backend/requirements.txt
README.md
```

## Purpose
This is a recovery build focused on restoring a known-stable operating baseline. It removes experimental frontend complexity and uses a hardened FastAPI backend that always returns valid structured JSON from `/run`.

## Deployment Instructions For Render

### Backend Web Service
1. Upload this ZIP contents to GitHub.
2. In Render, create or update the backend service.
3. Root directory: `backend`
4. Build command:
   ```text
   pip install -r requirements.txt
   ```
5. Start command:
   ```text
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
6. Environment variables:
   ```text
   OPENAI_API_KEY=your_key
   OPENAI_MODEL=gpt-4o-mini
   ANTHROPIC_API_KEY=optional
   ANTHROPIC_MODEL=claude-3-5-sonnet-latest
   ```

### Frontend Static Site
1. Root directory: `frontend`
2. Publish directory: `.`
3. The frontend is configured to call:
   ```text
   https://executive-engine-os.onrender.com
   ```

## Test Checklist

Backend:

```text
GET /
GET /health
GET /debug
POST /run
```

Required `/run` response shape:

```json
{
  "decision": "...",
  "next_move": "...",
  "actions": ["...", "...", "..."],
  "risk": "...",
  "priority": "High",
  "provider_used": "...",
  "status": "success"
}
```

Frontend:

```text
Loads successfully
Connects to backend
Sends command to /run
Displays NEXT MOVE first
Displays DECISION second
Displays ACTION STEPS third
Displays RISK fourth
Displays PRIORITY fifth
Shows loading state
Shows clear API/backend error state
```

## Known Limitations

- No Supabase changes.
- No memory expansion.
- No advanced dashboard features.
- If OpenAI is unavailable, the backend returns a local structured fallback so `/run` does not crash.
- Claude is fallback only and cannot break `/run`.
- The frontend is intentionally simple to support recovery testing.
