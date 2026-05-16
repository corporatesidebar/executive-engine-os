# Test Checklist — V35140 Guided Workflow Operating Loop Fix

1. Deploy frontend only.
2. Confirm no backend files are included.
3. Confirm the approved four-column layout loads.
4. Confirm dark sidebar is preserved.
5. Confirm main command area is preserved.
6. Submit a command.
7. Confirm POST goes to https://executive-engine-os.onrender.com/run.
8. Confirm loading state appears.
9. Confirm user message appears as a compact right-side bubble.
10. Confirm assistant response appears as a left-side guided workflow card.
11. Confirm response starts with Clear Answer.
12. Confirm response includes Why It Matters.
13. Confirm response includes Do This Next.
14. Confirm action steps render as task rows with status styling.
15. Confirm ready assets render as cards.
16. Confirm risk renders as a warning card with mitigation.
17. Confirm Continue with recommended command submits the recommended command.
18. Confirm Turn into action plan submits a follow-up command.
19. Confirm Draft asset submits a follow-up command.
20. Confirm Save decision updates runtime state.
21. Confirm sidebar Decisions view shows decision runtime data.
22. Confirm sidebar Actions/Team Pulse/Meeting Prep views show action runtime data.
23. Confirm Ready Assets/Files view shows asset runtime data.
24. Confirm Risk Monitor view shows risk runtime data.
25. Confirm Context/Upload Context view shows latest command and thread data.
26. Confirm Executive Summary updates from latest response.
27. Confirm Executive Intelligence shows current focus, active risk, follow-up, and what changed.
28. Confirm follow-up input remains functional.
29. Confirm API URL was not changed.
30. Confirm /run contract was not changed.
