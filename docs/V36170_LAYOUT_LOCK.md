# V36170 — Layout Lock + Clean Frontend

## Purpose
Fix the polluted frontend layout and lock the correct structure.

## Structure
- Left nav: operating categories
- Center: The Engine command panel + Top Priorities + Action Workspace
- Right rail: ACTIONS
- Frontend split into:
  - /frontend/index.html
  - /frontend/styles.css
  - /frontend/app.js

## Removed
- old light layout fragments
- duplicate hero sections
- old quick capture cards
- missing right rail state
- polluted single-file frontend leftovers

## Preserved
- backend routes
- action capture
- action command
- health/test routes
