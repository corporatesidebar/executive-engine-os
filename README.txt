Executive Engine OS V88

Fixes:
- Optimizes feedback speed.
- Frontend now times out backend requests after 22 seconds and gives an immediate useful fallback.
- Backend timeout reduced from 40s to 18s.
- Backend max_tokens added to reduce response latency.
- Adds right rail section: Your Engine.
- Your Engine shows latest 20 chats and lets you reopen them.
- Keeps simplified V87 flow, pages, Profile, Content Studio, Learning, Action Queue, Recent Decisions, noindex files.

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
