# Executive Engine OS V95

BUILD V95 — Stability + Memory-Driven Execution Loop

IMPORTANT:
No bot team.
No external automation.
No autonomous auto-loop.
Manual execution only.

V95 locks:
1. /run always returns valid JSON.
2. /health verifies backend status.
3. /run-test verifies a real manual test output.
4. /memory returns DB memory.
5. Last 3 memory items / runs / decisions injected into prompt.
6. System prompt acts as elite COO / operator.
7. Frontend stays compatible.
8. Auto-loop route exists but is disabled into manual loop planning only.

Architecture:
Memory -> Decision -> Action -> Memory -> Repeat

Endpoints:
- GET /health
- GET /debug
- GET /schema
- POST /run
- POST /run-test
- GET /memory
- GET /memory-summary
- GET /recent-runs
- GET /actions
- POST /save-action
- GET /decisions
- POST /save-decision
- GET /profile
- POST /profile
- POST /auto-loop  [manual-only in V95]
- POST /stability-check

Deploy backend:
Render -> executive-engine-os -> Clear build cache & deploy

Test:
https://executive-engine-os.onrender.com/health
https://executive-engine-os.onrender.com/stability-check
POST /run-test
