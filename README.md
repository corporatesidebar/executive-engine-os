# Executive Engine OS — V35140 Frontend Layout Restore

## Version
V35140 — Frontend Layout Restore / Layout-Locked Runtime Functionality

## Deployment Type
Frontend only.

## Backend URL Preserved
https://executive-engine-os.onrender.com

## Source of Truth
This package uses the approved locked `frontend/index.html` as the base file. The layout was not recreated from a screenshot.

## What Changed
- Preserved the approved locked frontend layout.
- Added/confirmed real command execution against `/run`.
- Added structured assistant rendering in this order:
  1. NEXT MOVE
  2. DECISION
  3. ACTION STEPS
  4. READY ASSETS
  5. RISK
  6. PRIORITY
  7. RECOMMENDED COMMAND
- Updated live Executive Summary cards from the backend response.
- Added Enter-to-submit behavior for the main command input.
- Added Execute button behavior.
- Added follow-up input submit behavior.
- Preserved loading and error state behavior.

## What Was Not Touched
- Backend
- Supabase
- Database schema
- Provider routing
- API URL
- `/run` output contract
- Visual layout
- Columns
- Fonts
- Colors
- Spacing
- Card structure

## Deploy
Upload the contents of the `frontend/` folder to the frontend static service only.
