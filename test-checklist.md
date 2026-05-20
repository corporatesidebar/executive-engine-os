# Test Checklist

1. Deploy frontend only.
2. Confirm the page visually matches approved 28(1) four-column layout.
3. Confirm there is no large blank white page area under the app at desktop width.
4. Confirm command input submits to https://executive-engine-os.onrender.com/run.
5. Confirm Enter submits from the command input.
6. Confirm Clear empties the command input.
7. Confirm user command appears in the thread.
8. Confirm assistant response renders as guided workflow software, not raw backend fields.
9. Confirm response shows Clear Answer, Why it matters, Do this next, Decision, Priority, task rows, asset cards, risk block, and recommended command.
10. Confirm Continue with recommended command submits the recommended command to /run.
11. Confirm Turn into action plan adds an action-plan workflow card.
12. Confirm Draft asset adds an asset-focused workflow card and updates asset state.
13. Confirm Save decision captures the decision and updates runtime state.
14. Confirm Executive Summary updates from runtime response.
15. Confirm Executive Intelligence updates from runtime response.
16. Confirm sidebar clicks use runtime state for Decisions, Risk Monitor, and Active Projects/Strategy workspace.
17. Confirm backend, Supabase, DB, API URL, /run contract, and provider routing were not touched.
