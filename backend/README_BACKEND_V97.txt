# Executive Engine OS V97

BUILD V97 — RIGHT SIDEBAR DB POLISH + DUPLICATE CONTROL

Backend:
- /actions returns deduped action rows.
- /decisions returns deduped decision rows.
- /save-action prevents duplicate open actions.
- /save-decision prevents duplicate saved decisions.
- /engine-state returns clean right sidebar state:
  - today_focus
  - your_engine
  - open_actions
  - recent_decisions
  - memory_items

Still locked:
- No bots
- No automation
- Manual execution only
- No Figma yet

Upload/replace backend:
- backend/main.py
- backend/requirements.txt
- backend/runtime.txt
- backend/README_BACKEND_V97.txt
