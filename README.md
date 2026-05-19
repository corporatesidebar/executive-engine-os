# Executive Engine OS V36170 — Functional Command Centre

Scope: functional frontend + FastAPI backend while preserving the approved three-column layout direction.

## What is functional
- All sidebar navigation buttons clickable
- Execute command button clickable
- Clear button clickable
- Category auto-select + manual override
- Command thread stores latest items at top
- User input followed by system response
- Filter button clickable
- Export button downloads JSON
- View Full Detail opens modal
- All right-side panel buttons clickable
- Right-side list items clickable/checkable
- Pressure score updates from system response
- Local fallback intelligence works if backend is unavailable

## Backend
Routes:
- GET /
- GET /health
- GET /debug
- GET /providers
- GET /test-report-json
- POST /run

## Local backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Frontend API URL
By default frontend points to:
`https://executive-engine-os.onrender.com`

For local backend, add before app.js in index.html:
```html
<script>window.EXECUTIVE_ENGINE_API_URL='http://127.0.0.1:8000'</script>
```

## Deploy rules
Do not delete stable backups. Deploy to a branch or staging service first.
