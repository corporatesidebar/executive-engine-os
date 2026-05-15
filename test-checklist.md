# Executive Engine OS — V35140 Frontend Layout Restore Test Checklist

## Frontend Visual Lock
1. Frontend loads.
2. Approved layout is preserved.
3. Dark left sidebar is preserved.
4. Main command/workspace column is preserved.
5. Executive Summary middle column is preserved.
6. Executive Intelligence right column is preserved.
7. Fonts are unchanged.
8. Colors are unchanged.
9. Card structure is unchanged.
10. Spacing/columns are unchanged.

## Runtime Functionality
11. Command input works.
12. Enter submits from the main command input.
13. Execute button submits.
14. User command renders in the conversation stream.
15. Loading state appears while request is running.
16. POST goes to https://executive-engine-os.onrender.com/run.
17. Error state appears if request fails.
18. Assistant response renders in the conversation stream.
19. Executive Summary cards update from the backend response.
20. Follow-up input submits.

## Output Contract Rendering Order
21. NEXT MOVE renders.
22. DECISION renders.
23. ACTION STEPS renders.
24. READY ASSETS renders.
25. RISK renders.
26. PRIORITY renders.
27. RECOMMENDED COMMAND renders.

## Preservation Checks
28. Backend not changed.
29. API URL not changed.
30. `/run` contract preserved.
31. Supabase not touched.
32. DB schema not touched.
33. Provider routing not touched.
