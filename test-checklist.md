# V35150A Test Checklist

## Deployment Rules
- [ ] Backend only
- [ ] Do not touch frontend
- [ ] Do not touch DB
- [ ] Do not touch Supabase
- [ ] Do not touch Claude
- [ ] Do not touch OpenAI routing
- [ ] Do not change `/run` logic
- [ ] Do not add V35160
- [ ] Do not add memory/actions

## Endpoint Tests
- [ ] `GET /` returns service metadata
- [ ] `GET /health` returns status ok
- [ ] `GET /debug` returns contract fields
- [ ] `GET /test-report` loads browser test console
- [ ] `GET /test-report-json` returns JSON report
- [ ] `POST /run` returns HTTP 200

## Test Page UI
- [ ] Run Tests button exists
- [ ] Copy Results button exists
- [ ] PASS / FAIL rows display clearly
- [ ] Endpoint checks display
- [ ] Frontend reachability displays
- [ ] Backend reachability displays
- [ ] POST `/run` contract validation displays
- [ ] Output contract fields display

## Required `/run` Output Contract
- [ ] `next_move`
- [ ] `decision`
- [ ] `action_steps`
- [ ] `ready_assets`
- [ ] `risk`
- [ ] `priority`
- [ ] `recommended_command`
