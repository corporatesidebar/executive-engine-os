# Executive Engine OS — V37200 Execution Object Persistence + Workspace Engine

BACKEND ONLY.

## Structure

backend/
├── main.py
└── requirements.txt
README.md
test-checklist.md

## What this adds

- Persistent execution objects
- Persistent command threads
- Workspace state
- Ready-to-review asset queue
- Object status updates
- Object archiving
- V36800-compatible /run contract

## Endpoints

- GET /
- GET /health
- POST /run
- GET /workspace
- GET /workspace/objects
- GET /workspace/ready
- PATCH /workspace/objects/{object_id}
- POST /workspace/objects/{object_id}/archive
- GET /test-report
- GET /test-report-json

## Do not touch

- frontend
- layout
- navigation
- Supabase
- DB schema
- API URL
