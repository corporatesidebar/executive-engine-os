# Executive Engine OS — Clean Redeploy Package

Use this package after deleting the bad/extra root files.

Correct structure:

```text
/backend/main.py
/backend/requirements.txt
/frontend/index.html
/README.md
/render.yaml
/.gitignore
```

Important:
- There is intentionally NO `/index.html` in the repository root.
- Frontend Render static site:
  - Root Directory: `frontend`
  - Publish Directory: `.`
  - Build Command: empty
- Backend Render web service:
  - Root Directory: `backend`
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Backend HTML test console:
https://executive-engine-os.onrender.com/test-report

Backend JSON test report:
https://executive-engine-os.onrender.com/test-report-json
