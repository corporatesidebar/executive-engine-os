
# V36060 — First-Load UX + Backend Weight Reduction

## Goal
Make first page load feel human, fast, and usable.

## Changes
- Replaced generic first-load copy:
  - From: `Create or advance a workspace.`
  - To: `Hey Will, let’s Rock n Roll today.`
- Added lightweight backend route:
  - `GET /first-load`
- `/first-load` does not call OpenAI.
- `/first-load` does not call Supabase.
- Added frontend first-load fetch to stabilize the greeting after operator state loads.
- Preserved all existing routes and features.

## Why
The previous first-load state was technically correct but poor UX.
The system should feel ready, human, confident, and direct immediately.

## Later
Add rotating personalized greetings:
- fun
- positive
- contextual
- pressure-aware
- unique by day
