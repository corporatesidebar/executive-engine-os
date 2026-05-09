# V36030 Rollback

If cleanup causes problems:

1. Go to GitHub repo history.
2. Restore previous working files:
   - `backend/main.py`
   - `backend/requirements.txt`
   - `frontend/index.html`
   - `render.yaml`
3. Redeploy Render backend.
4. Redeploy Render frontend.
5. Test:
   - `/health`
   - `/run`
   - frontend load

## Rollback triggers

Rollback if:

- frontend does not load
- backend does not deploy
- `/run` breaks
- protected routes disappear
- database status breaks unexpectedly

## Expected safe state

Current project backup remains available:
- Drive backup
- uploaded project ZIP
- GitHub history
