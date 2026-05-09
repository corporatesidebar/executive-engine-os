# Executive Engine OS — V36020 Daily Utility Layer

Goal: get the system to where the owner can actually use it and benefit today, before deeper enhancement.

## Adds
- New frontend page: Daily Use
- New backend route: POST /daily-use
- New backend route: GET /daily-use-state
- New backend route: GET /how-to-use
- Daily operating plan:
  - do this first
  - top 3 moves
  - follow-up now
  - asset to create
  - decision needed
  - risk to watch
  - end-of-day review
- Push Top 3 to Action Queue

## Preserves
- Existing V35130/V36010 structure
- /run
- /health
- /debug
- /providers
- /test-report-json
- /db-status
- /demo-state
- Operating Layer page

## Macro test
Use this first every day:
'I have client follow-ups, a proposal to prepare, meetings coming up, and too many priorities. Tell me what to do first today.'

Promote only if it gives a useful first move and reduces thinking load.
