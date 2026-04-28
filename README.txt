Executive Engine OS V81

Purpose:
- Refines V80 into a more usable executive OS.
- Makes 5 workflow boxes larger/wider with bigger fonts.
- Removes visible dropdown confusion from bottom-left composer.
- Replaces dropdown with a clear Current Workflow pill.
- Workflow board is now the main selector and single source of truth.
- Left navigation links/pages are functional.
- Added simple page content/cards for Plan Today, Decision, Meeting, Personal/Misc.
- + Add New starts the selected workflow and focuses the chat box.
- Recent workflow cards load into chat input.
- Keeps all backend, run, search, profile, action queue, decisions, processing, robots/noindex.

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
