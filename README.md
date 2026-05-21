# Executive Engine OS — V36800 Structured Execution Object Engine

Deployment type: **Backend only**.

## Purpose
This backend upgrades `/run` to return the structured execution contract required by frontend V37100.

## Required `/run` fields returned
- `executive_summary`
- `next_move`
- `decision`
- `action_steps`
- `ready_assets`
- `risk`
- `priority`
- `recommended_command`
- `execution_objects`
- `primary_object`
- `deployment_sequence`
- `executive_scan`

## Not touched
- Frontend
- Layout
- Supabase
- DB schema
- Provider routing outside this backend contract

## Preserved endpoint
- `POST /run`

## Run locally
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Render start command
```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

If Render runs from inside the `backend` folder, use:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```
