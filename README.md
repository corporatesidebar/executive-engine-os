# Executive Engine OS — V35140 Real Frontend Runtime Controller

Frontend-only package.

## Purpose
Restore the approved screenshot layout while rebuilding the frontend state/controller layer so the interface behaves like functional software instead of a static mockup.

## Files
- `frontend/index.html`
- `README.md`
- `test-checklist.md`

## Scope
- Frontend only
- No backend files
- No database changes
- No Supabase changes
- No provider routing changes

## Backend URL Preserved
`https://executive-engine-os.onrender.com`

## Runtime Behavior
- Command input submits with Enter
- Execute button submits to `/run`
- Follow-up input submits to `/run`
- Sidebar navigation switches real frontend states/sections
- Command chips populate the command input and can be run
- Loading, success, and error states are visible
- Executive Summary cards update from the latest `/run` response
- Executive Intelligence panel updates from the latest response/context

## Output Order Preserved
1. NEXT MOVE
2. DECISION
3. ACTION STEPS
4. READY ASSETS
5. RISK
6. PRIORITY
7. RECOMMENDED COMMAND
