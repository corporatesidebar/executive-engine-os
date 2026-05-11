# Executive Engine OS — V35080 Restore Package

Restore source: uploaded GitHub ZIP `executive-engine-os-main.zip`.

## Restored baseline
- Project: Executive Engine OS / WW OS
- Restored version: V35080 from V35060 verified base
- Backend URL used by frontend: `https://executive-engine-os.onrender.com`
- Frontend Render static site should serve `/frontend/index.html`
- Backend Render web service should serve `/backend/main.py`

## Restore decision
Use this package as the active restore point. It keeps the existing V35080 output guard/workspace cleanup build, but corrects provider routing to match the Chat #1 restore rule:

- OpenAI is the safe default.
- Claude is fallback only in auto mode.
- If Claude is explicitly requested and fails, the backend falls back to OpenAI.
- Claude failure/credits must not break `/run`.

## Preserved routes
- `/`
- `/health`
- `/debug`
- `/test-report`
- `/test-report-json`
- `/providers`
- `/run`
- `/router-preview`
- `/create-workspace`
- `/workspace-state`
- `/workspace-summary`
- `/operator-scan`
- `/operator-state`
- `/daily-briefing`
- `/pressure-monitor`
- `/stalled-workflows`
- `/attention-feed`
- `/workspace-reset`
- `/clear-workspace`
- `/reset-state`
- `/stabilize-workspace`
- `/quality-state`
- `/purge-pollution`
- `/pollution-audit`

## Upload instructions
Upload the entire folder structure to GitHub:

```text
/backend/main.py
/backend/requirements.txt
/frontend/index.html
/render.yaml
/README.md
/RESTORE_CONTEXT_V35080.md
```

Do not add a root `/index.html`.

## Render settings
Frontend static site:
- Root Directory: `frontend`
- Publish Directory: `.`
- Build Command: empty

Backend web service:
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Post-upload test
Run these after Render redeploys:

1. `GET /health`
2. `GET /test-report-json`
3. `GET /providers`
4. `GET /quality-state`
5. `POST /run` with provider `openai`

Expected result: valid JSON, no Claude dependency, no provider/error language polluting the workspace.
