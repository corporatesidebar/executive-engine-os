# Executive Engine OS — V36530 Continuity + Memory Engine

Backend-only build.

## What this adds

- Persistent workspace memory
- Active workflow persistence
- Recent decision memory
- Operator state tracking
- Open-loop tracking
- Recent asset tracking
- Context retrieval before response generation
- Workflow continuation instead of stateless chat
- `/engine-state`
- `/operator-scan`
- `/memory`
- `/workflow`

## What this does NOT change

- No frontend redesign
- No navigation changes
- No layout changes
- No sidebar changes
- No API URL changes

## Required `/run` contract preserved

- next_move
- decision
- action_steps
- ready_assets
- risk
- priority
- recommended_command
- provider_used
- status

## Deploy

Render start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Verify

```text
https://executive-engine-os.onrender.com/health
```

Should return:

```json
{
  "status": "ok",
  "version": "V36530-Continuity-Memory-Engine"
}
```

## Test

Use this command in the app:

```text
Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.
```

Then open:

```text
https://executive-engine-os.onrender.com/engine-state
```

You should see active workflow, recent decision, open loops, and operator state.
