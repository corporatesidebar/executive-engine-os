# Executive Engine OS — V35140 Runtime Functionality Layer

Frontend-only build.

## Scope
This package rebuilds the frontend runtime behavior while preserving the approved layout direction and locked backend connection.

## Files
- `frontend/index.html`
- `README.md`
- `test-checklist.md`

## Preserved
- Backend API URL: `https://executive-engine-os.onrender.com`
- POST route: `/run`
- Output order:
  1. NEXT MOVE
  2. DECISION
  3. ACTION STEPS
  4. READY ASSETS
  5. RISK
  6. PRIORITY
  7. RECOMMENDED COMMAND

## Not touched
- Backend
- Supabase
- DB schema
- Provider routing
- OpenAI / Claude routing
