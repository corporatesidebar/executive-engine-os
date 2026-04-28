Executive Engine OS V90

Fixes:
- Longer, fuller executive responses.
- Backend timeout increased to 35s.
- Backend max_tokens increased to 2200.
- Prompt strengthened so output does not feel shallow.
- Right sidebar cleaned up:
  - One-line rows.
  - Clear clickable chips: Open / Use / Run / Add / Save.
  - Your Engine is clearer: “Recent chats. Click a row to reopen.”
  - Action Queue and Recent Decisions are easier to scan.
  - Today’s Focus is cleaner and clickable.
- Strategic detail remains visible by default.

Upload:
- frontend/index.html
- frontend/robots.txt
- frontend/_headers
- backend/main.py
- backend/requirements.txt

Deploy:
1. Commit changes.
2. Render backend -> Manual Deploy.
3. Render frontend -> Clear cache & deploy.
4. Hard refresh: Ctrl + Shift + R.
