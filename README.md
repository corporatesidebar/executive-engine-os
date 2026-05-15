# Executive Engine OS — Frontend Runtime Controller

Frontend-only build for Executive Engine OS.

## Current Stable Lock

- Backend: V35150B locked stable
- Backend URL: https://executive-engine-os.onrender.com
- Frontend URL: https://executive-engine-frontend.onrender.com/

## What This Package Contains

```text
frontend/index.html
README.md
test-checklist.md
```

## What This Build Does

This build converts the approved Executive Engine OS layout from a static mockup into a real frontend runtime experience while preserving the visual structure:

- Dark left sidebar
- White main workspace
- Three-column structure
- Main workflow/chat area
- Executive Summary column
- Executive Intelligence right panel
- Orange Execute button
- Premium SaaS style

## Backend/API Rules

This package does not include backend files and does not change:

- Backend
- API URL
- /run contract
- Supabase
- DB schema
- Provider routing

The frontend posts to:

```text
https://executive-engine-os.onrender.com/run
```

## State Model

State is held in the browser runtime inside `index.html`:

- `messages`: user and assistant messages displayed as conversation bubbles
- `responses`: normalized backend responses stored for Decisions, Actions, Assets, and Risks sections
- `latest`: latest normalized `/run` response used to update Executive Summary and Executive Intelligence
- `threadId`: generated client-side thread identifier for continuing follow-up context
- `loading`: disables Execute button and renders loading bubble during `/run`
- `error`: renders visible error bubble if the request fails

## Response Contract Render Order

Backend response fields render in this exact order:

1. NEXT MOVE
2. DECISION
3. ACTION STEPS
4. READY ASSETS
5. RISK
6. PRIORITY
7. RECOMMENDED COMMAND

Missing fields are displayed as `Not returned by backend.` rather than silently failing.
