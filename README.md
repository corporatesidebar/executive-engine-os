# Executive Engine V37100 — Real Frontend State Controller

Frontend-only clean package.

Files:
- index.html
- styles.css
- app.js
- README.md

Base:
V37050 visual/layout shell.

Runtime:
- Single centralized app state
- One renderApp() pipeline
- Live POST to https://executive-engine-os.onrender.com/run
- Loading message is replaced by success/error state
- Backend response is parsed into executive fields
- Execution objects render as compact cards
- Right rail and executive summary sync from latest backend response

Deploy:
Upload these four files as the frontend root.
