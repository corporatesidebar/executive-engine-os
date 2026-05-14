# V35150B Test Checklist

## Backend-only package check
- [ ] ZIP contains `backend/main.py`
- [ ] ZIP contains `backend/requirements.txt`
- [ ] ZIP contains `README.md`
- [ ] ZIP contains `test-checklist.md`
- [ ] ZIP does not contain frontend files
- [ ] ZIP does not contain database schema files

## Route preservation
After deploy, test:
- [ ] GET `/`
- [ ] GET `/health`
- [ ] GET `/debug`
- [ ] GET `/test-report`
- [ ] GET `/test-report-json`
- [ ] GET `/providers`
- [ ] GET `/db-status`
- [ ] GET `/workspace-state`
- [ ] GET `/operator-scan`
- [ ] GET `/save-flow-status`
- [ ] POST `/save-action`
- [ ] POST `/save-decision`
- [ ] POST `/save-asset`

## Required /run contract
POST `/run` with:

`Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.`

Confirm response includes:
- [ ] `next_move`
- [ ] `decision`
- [ ] `action_steps`
- [ ] `ready_assets`
- [ ] `risk`
- [ ] `priority`
- [ ] `recommended_command`

Confirm backward-compatible keys still exist:
- [ ] `what_to_do_now`
- [ ] `actions`
- [ ] `asset`
- [ ] `follow_up`
- [ ] `provider_used`
- [ ] `router`
- [ ] `active_context`
- [ ] `workspace`
- [ ] `operator_state`

## Quality check
- [ ] Response is specific to the auto loan dealership input
- [ ] Response is executive-grade and business-focused
- [ ] No generic filler
- [ ] No vague motivational language
- [ ] Action steps are practical
- [ ] Ready assets name a useful asset
- [ ] Recommended command is usable

## Decision after testing
- [ ] HOLD if routes fail
- [ ] FIX if contract fields are missing
- [ ] PROMOTE if route surface and `/run` contract pass
