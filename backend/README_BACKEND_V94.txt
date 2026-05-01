# Executive Engine OS V94 Backend

BUILD V94 — Stability + Memory-Driven Execution Loop

Adds:
- Memory summary injected into every /run prompt.
- Automatic memory item creation after saved runs.
- Execution loop object returned in every response.
- /memory-summary endpoint.
- /stability-check endpoint.
- V94 schema addition: execution_loops table.
- Keeps all V93/V92 endpoints compatible.

Backend endpoints:
- /health
- /debug
- /schema
- /run
- /auto-loop
- /memory
- /memory-summary
- /stability-check
- /recent-runs
- /actions
- /save-action
- /decisions
- /save-decision
- /profile

Deploy:
1. Upload backend files.
2. Run supabase_schema_v94.sql in Supabase SQL editor.
3. Render executive-engine-os -> Clear build cache & deploy.
4. Test /health and /stability-check.
