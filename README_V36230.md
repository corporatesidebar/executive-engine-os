# V36230 — Command Centre Brain Upgrade

Backend-focused upgrade. Frontend layout/design preserved.

## Changed
- Upgraded `/run` response intelligence.
- Added stronger command classification across: proposals, meetings, strategy, tasks, calendar, risks, documents, media/advertising, content creation, team support, talent, and general commands.
- Improved local fallback so responses remain useful even without OpenAI.
- Strengthened OpenAI system prompt for executive-grade outputs.
- Preserved required `/run` contract:
  - next_move
  - decision
  - action_steps
  - ready_assets
  - risk
  - priority
  - recommended_command

## Deploy
Upload this ZIP to GitHub or replace the existing files, then deploy latest commit on Render.
