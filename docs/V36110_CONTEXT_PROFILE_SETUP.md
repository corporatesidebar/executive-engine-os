
# V36110 — Context Profile + Setup

## Purpose
Make Executive Engine outputs less generic by teaching it the user's role, company, priorities, active projects, people, risks, and goals.

## Adds
- POST /profile-setup
- GET /profile-state
- POST /profile-aware-flow
- Frontend page: Profile Setup
- Saves profile into ACTIVE_CONTEXT
- Adds profile-aware run path

## Why
Memory is more useful when the system knows what context matters.

## Promotion Standard
After saving a profile, the system should produce answers that are more specific to the user/company context.
