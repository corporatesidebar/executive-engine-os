Executive Engine OS V75

Purpose:
- Smooth GUI transitions
- Refined interaction polish
- Autosave draft input
- Rename current thread
- Duplicate current thread
- Better copy notification
- Search Escape clears search
- More command palette commands
- Frontend robots.txt disallows indexing
- Meta robots noindex/nofollow
- Static _headers includes X-Robots-Tag
- Backend /robots.txt disallows indexing

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

Go-live privacy:
- robots.txt disallows all crawlers
- meta robots blocks indexing
- X-Robots-Tag blocks indexing where supported

Test:
1. Open /robots.txt on frontend
2. Run prompt
3. Rename thread
4. Duplicate thread
5. Search then press Escape
6. Refresh page and confirm draft restores
