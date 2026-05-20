# Executive Engine OS — 2026-05-20 V36500 Intelligence Architecture

Backend-only package.

## What this builds

Executive Intelligence Architecture:

- continuity
- memory
- operational graphing
- workflow persistence
- pressure detection
- intelligent routing
- contextual reasoning
- operational sequencing
- executive communication generation
- proactive execution support

## Preserved contract

`POST /run` returns:

- next_move
- decision
- action_steps
- ready_assets
- risk
- priority
- recommended_command
- provider_used
- status

Additional context fields are included for the frontend if needed:

- router
- active_context
- workspace

## Files

```text
backend/main.py
backend/requirements.txt
README.md
```

## Local run

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## Render

Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Environment variable:

```text
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
```

If no OpenAI key is present, deterministic local intelligence fallback still returns the required contract.

## Test command

```bash
curl -X POST https://executive-engine-os.onrender.com/run \
  -H "Content-Type: application/json" \
  -d '{"input":"Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.","mode":"execution","brain":"revenue","output_type":"proposal","depth":"standard"}'
```

## Important

This package does not change frontend layout, navigation, sidebars, or design.
