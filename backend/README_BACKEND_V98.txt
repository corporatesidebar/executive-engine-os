# Executive Engine OS V98

BUILD V98 — PROFILE-AWARE OUTPUT

Backend:
- Adds default founder/operator profile context.
- Injects saved profile into every /run prompt.
- Uses profile even when user has not saved one yet.
- Adds /profile-status endpoint.
- Keeps V97 duplicate control and /engine-state.
- Keeps manual execution only.
- No bots.
- No automation.
- No Figma yet.

Upload/replace backend:
- backend/main.py
- backend/requirements.txt
- backend/runtime.txt
- backend/README_BACKEND_V98.txt

Test:
- /health
- /profile-status
- /project-context
- /run
