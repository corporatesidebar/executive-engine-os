# Executive Engine OS — V36200 System Build

Built from Commit 0a9926b stable backup.

## What is included
- Screenshot-aligned four-column executive cockpit frontend
- Functional command input and follow-up input
- Clickable sidebar/chips
- Live `/run` integration
- Backend contract: `next_move`, `decision`, `action_steps`, `ready_assets`, `risk`, `priority`, `recommended_command`
- Strong local fallback intelligence if OpenAI key is unavailable

## Deploy
Backend: deploy `/backend` to Render FastAPI.
Frontend: deploy `/frontend` as static site.
