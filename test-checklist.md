# V35150 Backend Output Contract Test Checklist

## Backend-only verification

- [ ] ZIP contains `backend/main.py`.
- [ ] ZIP contains `backend/requirements.txt`.
- [ ] ZIP contains `README.md`.
- [ ] ZIP contains `test-checklist.md`.
- [ ] ZIP does not contain `frontend/index.html`.
- [ ] No DB files included.
- [ ] No Supabase files included.
- [ ] No memory feature added.
- [ ] No V35160 features added.

## Endpoint verification

- [ ] `GET /` returns service status.
- [ ] `GET /health` returns `status: ok`.
- [ ] `POST /run` returns HTTP 200.
- [ ] `POST /run` returns valid JSON.
- [ ] `POST /run` returns exactly these keys:
  - `next_move`
  - `decision`
  - `action_steps`
  - `ready_assets`
  - `risk`
  - `priority`
  - `recommended_command`
- [ ] `action_steps` is always an array.
- [ ] `ready_assets` is always an array.
- [ ] `priority` is always `High`, `Medium`, or `Low`.
- [ ] AI failure still returns the same JSON contract.

## Test command

```bash
curl -X POST https://executive-engine-os.onrender.com/run \
  -H "Content-Type: application/json" \
  -d '{"input":"Prepare me for a revenue meeting tomorrow","mode":"meeting"}'
```

## Expected result

A valid JSON object containing only the required V35150 fields.
