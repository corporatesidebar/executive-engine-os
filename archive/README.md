# Executive Engine OS V35060 — Recovery ZIP

This ZIP is a V35060 recovery package reconstructed from verified V35060 artifacts found in the File Library.

Important:
- This is NOT guaranteed to be the original ZIP byte-for-byte.
- It preserves the verified V35060 version name, route map, test-report behavior, and core product direction.
- Use this only as a recovery baseline if the original V35060 ZIP cannot be located.

Verified V35060 evidence:
- README_V35060 described Executive Operating Flow Stabilization.
- Critical test report showed version: 35060-executive-operating-flow-stabilization.
- Critical test report showed 5/5 backend tests passed.
- Critical test report listed restored routes and output schema.

Folder structure:
- frontend/index.html
- backend/main.py
- backend/requirements.txt
- docs/V35060_CRITICAL_TEST_EVIDENCE.txt
- docs/RECOVERY_NOTES.md
- test-checklist.md

Deployment:
Backend Render:
- Root directory: backend
- Build command: pip install -r requirements.txt
- Start command: uvicorn main:app --host 0.0.0.0 --port 10000

Frontend Render:
- Root directory: frontend
- Publish directory: .
- Static site using index.html

Environment variables:
- OPENAI_API_KEY
- OPENAI_MODEL=gpt-4o-mini

Do not:
- Delete the repo.
- Upload the ZIP directly to Render.
- Replace production until you inspect files.
- Assume this is the original lost ZIP.
