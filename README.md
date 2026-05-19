# Executive Engine OS — V36160 Executive Advantage Prototype

Full working prototype package for GitHub/Render testing.

## Files

- `backend/main.py` — FastAPI backend with `/run`, `/health`, `/workspace-state`, `/test-report-json`
- `backend/requirements.txt` — Python dependencies
- `frontend/index.html` — static frontend
- `frontend/style.css` — frontend styling
- `frontend/app.js` — frontend controller

## What this build does

- Preserves the required `/run` output contract:
  - `next_move`
  - `decision`
  - `action_steps`
  - `ready_assets`
  - `risk`
  - `priority`
  - `recommended_command`
- Adds intent/category routing.
- Creates workflow records from each command.
- Tracks open loops, risks, assets, decisions, pressure score, and operating thread.
- Includes optional OpenAI routing when `OPENAI_API_KEY` exists.
- Uses a deterministic operator-grade fallback when OpenAI is not configured.
- Frontend keeps the 4-column operating structure and connects to `/run`.

## Backend local run

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open:

```text
http://localhost:8000/health
```

## Frontend local run

Open `frontend/index.html` in browser, or serve it with any static host.

By default it calls:

```text
https://executive-engine-os.onrender.com
```

To test local backend, edit `frontend/app.js`:

```js
const API_URL = 'http://localhost:8000';
```

## Render deployment

Backend:

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Frontend:

- Root directory: `frontend`
- Static publish directory: `.`

## Optional AI

Set environment variable:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

If no key exists, the fallback engine still works.
