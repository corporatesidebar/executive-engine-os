# Executive Engine OS V96.3 Quality Fix

Problem:
V96.2 technically worked, but the output was still generic:
- user feedback
- product roadmap
- market trends
- product development team

Fix:
- Hard project context strengthened
- Generic prior memory filtered from prompt
- Project-specific directive added for Executive Engine OS prompts
- Forbidden generic phrases added
- New /quality-test endpoint added
- Fallback now returns project-specific execution validation plan

Upload/replace:
- backend/main.py
- backend/requirements.txt
- backend/runtime.txt
- backend/README_BACKEND_V96_3_QUALITY_FIX.txt

Deploy:
Render -> executive-engine-os -> Manual Deploy -> Clear build cache & deploy

Test:
- /health
- /quality-test
- frontend prompt: What should I focus on today to move Executive Engine OS forward?

Expected:
Answer must mention:
- /run
- /memory
- /save-action
- /save-decision
- /actions
- /decisions
- frontend right panel
- Supabase persistence
- manual execution only
