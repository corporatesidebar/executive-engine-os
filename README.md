# Executive Engine OS — V35150 Selective /run Quality Patch

## Decision
MERGE SELECTIVELY.

## Baseline preserved
Current backend route surface from V35130R is preserved. This package does not include frontend files, database schema files, Supabase keys, Render configuration, or provider routing changes.

## Reference used
`executive-engine-os-v35150-real-output-contract.zip` was used as a selective patch reference only.

## What changed
- Updated backend version label to `35150-selective-run-quality-on-v35130r`.
- Strengthened the `/run` system prompt with the V35150 required output contract.
- Added required contract enforcement for:
  - `next_move`
  - `decision`
  - `action_steps`
  - `ready_assets`
  - `risk`
  - `priority`
  - `recommended_command`
- Preserved backward-compatible keys including:
  - `what_to_do_now`
  - `actions`
  - `asset`
  - `follow_up`
  - `provider_used`
  - `router`
  - `active_context`
  - `workspace`
  - `operator_state`
- Added JSON normalization helpers for `action_steps`, `ready_assets`, `priority`, and `recommended_command`.
- Updated `/test-report-json` schema metadata to expose the required `/run` contract.

## What was not touched
- Frontend files were not created.
- Supabase keys were not touched.
- DB schema was not touched.
- Provider routing was not changed.
- API URL was not changed.
- Workspace/save/test routes were preserved.

## Diagnosis
The V35130R backend already had strong route coverage and workspace/save/DB support, but `/run` responses did not always expose the V35150 contract fields expected by the frontend and recovery path. The existing payload used `actions` and `asset`, but did not reliably guarantee `action_steps`, `ready_assets`, or `recommended_command`.

## Recommended version name
V35150B — Selective /run Response Quality Contract Patch
