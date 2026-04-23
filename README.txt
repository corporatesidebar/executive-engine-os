Executive Engine merged rebuild

Use ONE Render Web Service only.

Render settings:
- Root Directory: backend
- Build Command: pip install -r requirements.txt
- Start Command: uvicorn main:app --host 0.0.0.0 --port 10000

Upload both folders from this zip:
- frontend
- backend

This build serves the frontend from the backend.
The button posts to /api/command on the same service.
