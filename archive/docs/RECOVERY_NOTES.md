# Recovery Notes

Decision:
Use this ZIP only if the original V35060 files are not available.

Risk:
This is a reconstruction from verified V35060 evidence, not the original deleted ZIP.

Action:
1. Extract locally.
2. Compare backend/main.py and frontend/index.html before replacing anything live.
3. Deploy to a test branch/service first if possible.
4. Confirm:
   - GET /
   - GET /health
   - GET /debug
   - GET /test-report-json
   - GET /providers
   - POST /run
5. Promote only if tests pass.

Priority:
High — stabilize from V35060 before expanding into V35100 or cockpit UX work.
