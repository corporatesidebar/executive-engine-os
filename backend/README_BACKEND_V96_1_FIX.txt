# Executive Engine OS V96.1 Route Fix

Problem:
Render failed with:
TypeError: FastAPI.get() takes 2 positional arguments but 4 were given

Cause:
A bad decorator was generated:
@app.get("/engine-state", "/project-context", "/memory")

Fix:
The route is corrected back to:
@app.get("/memory")

Upload/replace:
- backend/main.py
- backend/requirements.txt
- backend/runtime.txt
- backend/README_BACKEND_V96_1_FIX.txt

Deploy:
Render -> executive-engine-os -> Manual Deploy -> Clear build cache & deploy

Test:
- /health
- /project-context
- /memory
