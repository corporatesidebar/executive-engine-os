Executive Engine OS V61 Layout Fix

Changes:
- Fixes missing/hidden composer input on empty screen
- Keeps Databricks-style top nav
- Makes input visible under hero prompt
- Input moves to bottom after first message
- Reduces right rail clutter
- Keeps search, profile/resume, automation, memory, history, backend test

Upload:
- frontend/index.html
- backend/main.py
- backend/requirements.txt

Deploy:
1. Commit changes
2. Render backend -> Manual Deploy
3. Render frontend -> Clear cache & deploy
4. Hard refresh: Ctrl + Shift + R
