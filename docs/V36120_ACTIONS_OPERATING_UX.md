
# V36120 — ACTIONS Operating UX

## Purpose
Replace disconnected dashboards/projects with one operating model: ACTIONS.

## Adds
- Left sidebar titled ACTIONS
- New Action
- Search actions
- Command Centre home
- Persistent bottom quick capture
- Action chips: Meeting, Proposal, Strategy, Follow-Up, Execution, Notes
- Auto action creation
- Short summary first
- View Detailed Brief
- Editable draft/notes
- AI-style actions:
  - Save
  - AI Polish
  - Client Ready
  - Shorten

## Backend
- POST /action-capture
- GET /actions-lite
- GET /action-lite/{action_id}

## Product direction
Executives do not manage "projects." They manage active operational ACTIONS.
