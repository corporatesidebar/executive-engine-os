# V35140 Frontend Workflow State Model Test Checklist

## Scope
Frontend only.

## Must Pass
1. Frontend loads successfully.
2. Approved layout remains visually intact.
3. Dark sidebar is preserved.
4. Main command area is preserved.
5. Executive Summary column is preserved.
6. Executive Intelligence column is preserved.
7. API URL remains `https://executive-engine-os.onrender.com`.
8. Main command submits to `/run`.
9. Enter submits the main command.
10. Execute button submits the main command.
11. User command appears as a compact right-side bubble.
12. Assistant response appears as a compact left-side structured card.
13. Assistant card renders sections in this exact order:
    - NEXT MOVE
    - DECISION
    - ACTION STEPS
    - READY ASSETS
    - RISK
    - PRIORITY
    - RECOMMENDED COMMAND
14. Response output does not render as pasted/plain document-style text.
15. Next Action button appears after assistant response.
16. Next Action button loads recommended command into the follow-up input.
17. Follow-up input remains pinned at the bottom of the workflow panel.
18. Follow-up input submits and continues the same conversation thread.
19. Command sidebar view shows live conversation.
20. Decisions sidebar view shows runtime decisions.
21. Action Workspace sidebar view shows runtime action steps.
22. Ready Assets sidebar view shows runtime assets.
23. Risk Monitor sidebar view shows runtime risks.
24. Context sidebar view shows active command/context.
25. Executive Summary updates from latest response.
26. Executive Intelligence updates from latest response/context.
27. Static/fake runtime content is removed or replaced with runtime state.
28. Backend was not touched.
29. Supabase/DB were not touched.
30. Provider routing was not touched.
