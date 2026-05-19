# V35115 — Full Navigation Lock + Premium UX

Frontend-focused build. Backend files are included for complete upload package but are unchanged from V35090 stabilization.

## Purpose
This build fixes the V35111/V35112 deployment confusion by making the full left navigation explicit and visible.

## Locked Navigation
Command:
- Today
- Daily Brief
- Run Command
- Meeting Prep
- Decisions

Intelligence:
- Operator Intelligence
- Strategy Board
- Risk Monitor
- Team Pulse
- Financial Snapshot

Resources:
- Workspace
- Action Queue
- Assets
- Files
- Notes

System:
- System Status

## Deployment Check
After deploy, the top-left brand must show: `V35115 Full Nav Lock`.

If it does not, Render is still serving an old frontend build.
