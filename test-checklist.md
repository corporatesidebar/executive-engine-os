# Test Checklist — V35160 Backend Response Intelligence Fix

## Deploy target
Backend Render service only.

## Do not touch
- Frontend
- DB
- Supabase
- Claude routing
- Deployment settings
- Layout
- Navigation

## Endpoint tests
Open:
```text
https://executive-engine-os.onrender.com/
https://executive-engine-os.onrender.com/health
https://executive-engine-os.onrender.com/debug
https://executive-engine-os.onrender.com/test-report
https://executive-engine-os.onrender.com/test-report-json
```

Expected:
- All routes return 200.
- Version reports `V35160-response-intelligence-fix`.
- `/test-report` has Run Tests and Copy JSON.

## /run contract test
POST to:
```text
https://executive-engine-os.onrender.com/run
```

Body:
```json
{
  "command": "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100."
}
```

Expected fields:
```text
next_move
decision
action_steps
ready_assets
risk
priority
recommended_command
provider_used
status
```

Expected behavior:
- Output is about Ontario auto-loan dealership proposal.
- Output includes actual proposal content in `ready_assets`.
- Output does not mention Costa Rica, relocation, residency, or unrelated job-search content.
- `action_steps` has 3-7 items.
- `ready_assets` is an array.
- `priority` is High, Medium, or Low.
- `status` is success.

## Decision
- PROMOTE only if all checks pass.
- FIX if any endpoint fails or proposal prompt returns unrelated content.
- HOLD if deployment is inconsistent.
