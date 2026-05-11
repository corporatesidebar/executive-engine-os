# Executive Engine OS — V35130 Real Executive Workflow

Purpose: move the product from a visual demo into a workflow-first executive operating experience.

## What changed
- Rebuilt the frontend around a clearer command-centre cockpit.
- Full navigation preserved.
- Every section now has seeded test content so the product does not feel empty.
- Added smoother transitions, radar/operator rail, better hierarchy, and less confusing workflow language.
- Run Command is now a focused ChatGPT-style work room with saved history.
- Today page shows pressure, open actions, assets, next-best action, and operating flow.
- Action Queue uses clear owner/due/priority task cards with checkboxes.
- Database page can check `/db-status`, `/db-items`, and `/db-test-write`.
- Backend prompt upgraded for real executive responses.
- Fallback output upgraded from generic provider failure to a usable executive rule-based response.
- Auto-loan proposal fallback no longer hijacks every generic proposal/SEO prompt.
- Added `/demo-state` for seeded UI/testing content.

## Deployment
Upload all folders/files to GitHub and redeploy both backend and frontend.

Expected backend version:
`35130-real-executive-workflow`

Expected frontend label:
`V35130 Real Workflow`

## DB env vars for Render backend
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- SUPABASE_TABLE=items

Use `/db-status` and `/db-test-write` to confirm persistence.
