Executive Engine OS V89

Fixes:
- Stops reverting to the too-short/fallback answer as quickly.
- Frontend timeout increased from 22s to 35s.
- Backend timeout increased from 18s to 28s.
- Backend max_tokens increased from 750 to 1400.
- Backend prompt now forces useful complete executive output, not shallow short output.
- Right sidebar is functional:
  - Your Engine chats reopen when clicked.
  - Today’s Focus has Use Focus / New Run.
  - Action Queue items can Run or Remove.
  - Action Queue can be cleared.
  - Recent Decisions can be clicked/used.
  - Recent Decisions can be cleared.
- Strategic detail now shows by default.

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
