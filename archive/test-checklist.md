# V35060 Recovery Test Checklist

Backend URL:
https://executive-engine-os.onrender.com

Required tests:
- [ ] GET /
- [ ] GET /health
- [ ] GET /debug
- [ ] GET /test-report-json
- [ ] GET /providers
- [ ] POST /run

Expected version:
35060-executive-operating-flow-stabilization

POST /run test body:
{
  "input": "Build proposal for Ontario auto loan dealership with SEO and Google Ads CPA under $100.",
  "category": "proposal"
}

Expected output includes:
- what_to_do_now
- decision
- next_move
- actions
- risk
- priority
- asset
- follow_up
- provider_used
- router
- active_context
- workspace
- operator_state
