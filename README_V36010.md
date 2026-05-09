# Executive Engine OS — V36010 Merge-Safe Executive Operating Layer

This build is based on the uploaded V35130 backup and is merge-safe.

## What changed
- Preserves the existing V35130 backend/frontend structure.
- Preserves existing routes including `/run`, `/health`, `/debug`, `/providers`, `/test-report-json`, `/db-status`, `/demo-state`, operator/workspace routes, and save routes.
- Adds new backend routes:
  - `POST /operating-layer`
  - `POST /daily-operating-layer`
  - `GET /operating-layer-state`
- Adds a new frontend page:
  - `Operating Layer`
- Adds macro-test output sections:
  - Today
  - Tomorrow
  - Decision Queue
  - Execution Queue
  - Meeting Intelligence
  - Strategy Insights
  - Risk Watch
  - Follow-Ups
  - Memory To Store

## What this does NOT do
- Does not change Supabase schema.
- Does not remove V35130 functionality.
- Does not replace `/run`.
- Does not touch Executive Engine deployment URLs.
- Does not require new env vars.

## Deploy
Upload the files/folders to GitHub, then redeploy Render frontend/backend.

## Test
1. Open `/health`
2. Open `/test-report-json`
3. Open `/operating-layer-state`
4. Open frontend.
5. Click `Operating Layer`.
6. Run a real executive situation.
7. Confirm output populates and can be pushed to Action Queue.
