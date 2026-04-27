Executive Engine OS V60 Databricks-Style Header

Changes:
- Rebuilds top nav/header to match the attached Databricks-style layout
- Left: menu + brand
- Center: large search bar
- Right: Test, New, spark menu, avatar
- Keeps nav/workflows inside the spark menu and sidebar
- Keeps global search functional
- Keeps V59 functional stability fixes
- Keeps input/composer, profile/resume, automation, systems, memory, and history

Upload:
- frontend/index.html
- backend/main.py
- backend/requirements.txt

Deploy:
1. Commit changes
2. Render backend -> Manual Deploy
3. Render frontend -> Clear cache & deploy
4. Hard refresh: Ctrl + Shift + R
