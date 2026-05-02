# Executive Engine OS V97

BUILD V97 — Frontend Memory Polish + Engine State

Purpose:
V97 keeps backend stability locked and adds a cleaner backend endpoint for frontend right-panel state.

No bot team.
No external automation.
Manual execution only.

Adds:
- /engine-state endpoint for frontend right sidebar
- Context remains injected from V96
- Version reports V97
- Compatible with existing /memory, /recent-runs, /actions, /decisions

Upload/replace:
- backend/main.py
- backend/requirements.txt
- backend/runtime.txt
- backend/README_BACKEND_V97.txt

Deploy backend:
Render -> executive-engine-os -> Clear build cache & deploy

Test:
- /health
- /engine-state
- /project-context
- /memory
