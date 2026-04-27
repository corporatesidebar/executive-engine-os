Executive Engine OS V65

Purpose:
- Make Executive Engine brand clickable to main page
- Refine UI and reduce busy feeling
- Style search bar and search results
- Style scrollbars
- Keep Run Engine button same width/height during loading
- Fixed composer height to prevent layout jump
- Reduce quick prompts and right-side clutter
- Keep V64 clickable status chips and automation features

Upload:
- frontend/index.html
- backend/main.py
- backend/requirements.txt

Deploy:
1. Commit changes
2. Render backend -> Manual Deploy
3. Render frontend -> Clear cache & deploy
4. Hard refresh: Ctrl + Shift + R

Test:
1. Click Executive Engine brand -> main page
2. Type prompt -> Run Engine
3. Confirm button size does not jump
4. Use search
5. Click status chips
