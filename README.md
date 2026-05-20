# Executive Engine OS — V36800 Structured Execution Object Engine

Package type:
- Backend upgrade
- Frontend response renderer helper
- Additive Supabase SQL

## What this fixes

The system was forcing operational intelligence into generic text cards. V36800 changes the product architecture so `/run` returns structured operational objects.

## Backend returns

- executive_scan
- execution_objects
- primary_object
- deployment_sequence
- memory_state
- legacy frontend-compatible keys

## Object types supported

- proposal
- outreach_sequence
- crm_pipeline
- kpi_scorecard
- deployment_checklist
- landing_page
- offer
- pricing_model
- operating_system
- delegation_map
- follow_up_system

## Install backend

Deploy `/backend` to Render.

Start command:

uvicorn main:app --host 0.0.0.0 --port $PORT

## Install frontend helper

Add after existing CSS/JS only if you are ready to render structured objects:

```html
<link rel="stylesheet" href="./structured-execution-renderer.css">
<script src="./structured-execution-renderer.js"></script>
```

Then, when `/run` returns data:

```js
if (data.renderer_mode === "structured_objects" && window.renderStructuredExecutionObjects) {
  responseContainer.innerHTML = window.renderStructuredExecutionObjects(data);
}
```

## Supabase

Run `/supabase/v36800_structured_execution_objects.sql`.

It is additive only.
