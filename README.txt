Executive Engine OS V78

Purpose:
- Fluid executive UX rebuild
- Removes visible redundancy/confusion
- Simplifies top bar to: Brand / Search / New
- Simplifies sidebar to core executive workflows only
- Replaces noisy chips with 3-step guide
- Uses one clear Need dropdown
- Removes Clear and visible depth dropdown
- Simplifies right rail to: Today's Focus, Action Queue, Recent Decisions
- Adds post-output action buttons:
  Add to Action Queue, Save Decision, Create Follow-Up, Run Deeper Analysis
- Keeps processing overlay, robots/noindex, command palette/search, profile, memory, backend logic

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
