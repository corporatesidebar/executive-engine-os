# RESTORE CONTEXT — Executive Engine OS V35090

Latest stable package: V35090 Stabilization Patch.

Backend version expected after deploy:
`35090-stabilization-patch`

Primary backend URL remains:
`https://executive-engine-os.onrender.com`

Primary frontend remains static HTML/CSS/JS in:
`/frontend/index.html`

Backend remains FastAPI in:
`/backend/main.py`

Provider logic:
- OpenAI-first is preserved.
- Claude can exist as configured, but must not break `/run`.
- If Claude fails or lacks credits, backend should return OpenAI or safe fallback.
- `provider_used` should reflect the successful route.

Stabilization fixes applied:
- `/run` quality patch now uses `req` correctly.
- `/autonomous-package` quality patch now uses `req` correctly.
- Workspace sanitizer compatibility restored.
- ACTIVE_CONTEXT is used consistently in quality-generated workspace paths.
- Timestamp shadow bug in autonomous package path fixed.

Do not rebuild from scratch unless explicitly requested.
