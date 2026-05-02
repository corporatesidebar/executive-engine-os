# Executive Engine OS V96.2 Clean Backend

This is a clean backend replacement that removes the broken multi-route decorators.

Fixes:
- Removes invalid @app.get("/project-context", "/memory")
- Removes invalid @app.get("/engine-state", "/project-context", "/memory")
- Keeps V95.2 stability
- Adds V96 project context injection
- Keeps Supabase memory
- Keeps manual execution only

Upload/replace:
- backend/main.py
- backend/requirements.txt
- backend/runtime.txt
- backend/README_BACKEND_V96_2_CLEAN.txt

Deploy:
Render -> executive-engine-os -> Manual Deploy -> Clear build cache & deploy

Test:
- /health
- /project-context
- /memory
- /run-test
