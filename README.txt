Executive Engine OS V80

Purpose:
- Changes Choose Workflow into 5 Notion-style workflow boxes/columns.
- Each workflow box shows up to 5 recent inputs for that workflow.
- If no recent inputs exist, it shows suggested starter inputs.
- Each workflow box has + Add New.
- Chat input box is directly below workflow boxes, not stuck at bottom.
- Keeps same layout and colours from V79.
- Keeps all V79 functionality: sidebar, dropdown, run, search, profile, action queue, recent decisions, processing overlay, robots/noindex.

Upload:
- frontend/index.html
- frontend/robots.txt
- frontend/_headers
- backend/main.py
- backend/requirements.txt

Deploy:
1. Commit changes
2. Render backend -> Manual Deploy
3. Render frontend -> Clear cache & deploy
4. Hard refresh: Ctrl + Shift + R
