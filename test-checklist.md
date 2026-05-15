# Executive Engine OS — Frontend Chat Rendering Test Checklist

## Visual preservation
1. Frontend loads successfully.
2. Approved dark sidebar remains unchanged.
3. Header remains unchanged.
4. Main command area remains unchanged.
5. Executive Summary column remains unchanged.
6. Executive Intelligence column remains unchanged.
7. Overall spacing, columns, cards, fonts, and colors remain visually consistent with the approved layout.

## Chat/workflow rendering
8. Enter a command in the top command box.
9. Click Execute.
10. Confirm the user command appears as a compact right-side message bubble.
11. Confirm the assistant response appears as a left-side structured bubble/card.
12. Confirm assistant output is compact and does not render as a long plain-text document.
13. Confirm previous messages remain readable in the workflow panel.
14. Confirm follow-up input remains pinned at the bottom of the workflow panel.

## `/run` contract rendering order
15. Confirm assistant response renders:
    - NEXT MOVE
    - DECISION
    - ACTION STEPS
    - READY ASSETS
    - RISK
    - PRIORITY
    - RECOMMENDED COMMAND

## Functionality
16. Confirm Enter submits from the main command box.
17. Confirm Execute submits from the main command box.
18. Confirm Enter submits from the follow-up input.
19. Confirm the follow-up send icon submits.
20. Confirm loading state appears while waiting.
21. Confirm error state appears if backend request fails.
22. Confirm POST goes to `https://executive-engine-os.onrender.com/run`.

## Safety checks
23. Backend not changed.
24. API URL not changed.
25. `/run` contract preserved.
26. Supabase not changed.
27. DB not changed.
28. Provider routing not changed.
