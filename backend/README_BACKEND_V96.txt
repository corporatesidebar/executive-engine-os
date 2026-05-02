# Executive Engine OS V96

BUILD V96 — PROJECT CONTEXT + RESPONSE QUALITY

Purpose:
V96 fixes generic output by injecting real Executive Engine OS project context into every /run prompt.

Adds:
- PROJECT_CONTEXT injected into backend prompt
- /project-context endpoint
- Response rules against generic SaaS advice
- Focus on Render backend, Supabase memory, frontend, manual execution
- No bot team
- No automation
- Figma after backend/output stability

Upload/replace:
- backend/main.py
- backend/requirements.txt
- backend/runtime.txt
- backend/README_BACKEND_V96.txt

Deploy:
Render -> executive-engine-os -> Manual Deploy -> Clear build cache & deploy

Test:
- /health
- /project-context
- /run-test
- /run with: What should I focus on today to move Executive Engine OS forward?

Expected:
- version: V96
- supabase_enabled: true
- project-specific output
