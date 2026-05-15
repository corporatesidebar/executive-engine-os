# Executive Engine OS — V35140 Guided Workflow Layer Fix

Deployment type: Frontend only.

Backend URL preserved: https://executive-engine-os.onrender.com

## What changed
- Added a guided frontend workflow layer inside the approved locked layout.
- Main chat now shows a clear answer, next action, suggested follow-up command, compact /run sections, and saved workflow preview after each response.
- User messages remain compact right-side bubbles.
- Assistant responses remain left-side structured workflow cards.
- Sidebar sections now render runtime state workspaces for Decisions, Action Workspace, Ready Assets, Risk Monitor, and Context.
- Executive Summary now summarizes the latest operating state from runtime response data.
- Executive Intelligence now shows current focus, active risk, recommended next move, and follow-up prompt from runtime state.
- Static/fake runtime content is replaced by state-driven content.

## What was not touched
- Backend files were not changed.
- API URL was not changed.
- /run contract was not changed.
- Supabase, DB schema, provider routing, columns, sidebar, fonts, spacing, and approved layout were not changed.
