Executive Engine OS V79

Purpose:
- Fixes all major visible buttons/pages by rebuilding frontend cleanly.
- Makes Ask / Execute selector prominent and styled.
- Removes confusing duplicate "What do you need?" vs "Need" issue:
  one source of truth = Choose Workflow cards + Need dropdown, synced together.
- Left nav works.
- Workflow cards work.
- Dropdown works.
- Run Engine works.
- Search works.
- Command palette works with Ctrl/Cmd+K.
- Profile page works.
- Action Queue works locally.
- Recent Decisions works locally.
- Post-output action buttons work.
- Processing overlay remains.
- robots/noindex remain.

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
