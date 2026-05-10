# Executive Engine OS — Rebuild Package

This package restores the minimum working project structure after files/folders were deleted.

## Folder Structure

```text
frontend/index.html
backend/main.py
backend/requirements.txt
README.md
```

## Render Backend Settings

Root Directory:

```text
backend
```

Build Command:

```text
pip install -r requirements.txt
```

Start Command:

```text
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Environment Variables:

```text
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini
```

## Render Frontend Settings

Root Directory:

```text
frontend
```

Publish Directory:

```text
.
```

## Important

In `frontend/index.html`, update this line if your backend URL is different:

```javascript
const API_BASE = "https://executive-engine-os.onrender.com";
```

## Backend Endpoints

```text
GET /
GET /health
GET /debug
POST /run
```
