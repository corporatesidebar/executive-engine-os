Executive Engine OS V76

Purpose:
- Adds clear Processing / Thinking state after Run Engine is pressed
- Adds processing overlay so user knows request is working
- Adds composer processing highlight
- Adds Run button loading state
- Changes top navigation background to black/navy to match left sidebar
- Keeps V75 smooth GUI, robots/noindex, thread rename/duplicate, autosave, command palette, go-live checks

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

Test:
1. Press Run Engine
2. Confirm Processing request overlay appears
3. Confirm Run button says Running
4. Confirm top nav is dark/navy
