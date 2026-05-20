# Test Checklist — V35160B

## Deploy scope
- [ ] Backend service only
- [ ] No frontend files deployed
- [ ] No database/Supabase changes
- [ ] No deployment setting changes

## Endpoint tests
- [ ] GET `/` returns 200 and version `V35160B-backend-response-comprehension-fix`
- [ ] GET `/health` returns 200
- [ ] GET `/debug` returns 200
- [ ] GET `/test-report` loads browser page
- [ ] GET `/test-report-json` returns JSON report
- [ ] POST `/run` returns 200

## `/run` contract
- [ ] `next_move`
- [ ] `decision`
- [ ] `action_steps`
- [ ] `ready_assets`
- [ ] `risk`
- [ ] `priority`
- [ ] `recommended_command`
- [ ] `provider_used`
- [ ] `status`

## Intelligence tests
Use prompt:
`Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.`

Expected:
- [ ] Intent is proposal
- [ ] Output is dealership / auto-loan / SEO / Google Ads proposal
- [ ] Output contains actual proposal-ready content
- [ ] Output does not mention Costa Rica
- [ ] Output does not mention relocation
- [ ] Output does not mention residency
- [ ] Output is concise enough to read in frontend cards

## Test page tools
- [ ] Run Tests button works
- [ ] Copy JSON button works
- [ ] PASS/FAIL is clear
