# Executive Engine OS — V36100 Working Prototype

## Purpose
This is a lean working prototype focused on the first real useful loop:

`command -> intelligence routing -> executive output -> follow-up -> operational continuity`

It is not a dashboard mockup. It is a working frontend + FastAPI backend that preserves the core idea of Executive Engine OS as a push-first executive operating layer.

## Files

```text
backend/main.py
backend/requirements.txt
frontend/index.html
frontend/styles.css
frontend/app.js
README.md
TEST_CHECKLIST.md
```

## Local Run

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend local URL:
```text
http://127.0.0.1:8000
```

### Frontend
Open:
```text
frontend/index.html
```

Or serve it:
```bash
cd frontend
python -m http.server 5173
```

Frontend local URL:
```text
http://127.0.0.1:5173
```

## Render Deployment

### Backend Render Settings
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Frontend Render Settings
- Root directory: `frontend`
- Publish directory: `.`
- Build command: leave blank for static site

## Environment Variables

Optional:
```text
OPENAI_API_KEY=your_key_here
```

If no OpenAI key exists, backend uses deterministic local executive intelligence logic so the app still works.

## Version
V36100 — Executive Workflow & Intelligence Working Prototype
