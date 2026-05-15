# Test Checklist — V35140 Guided Workflow Layer Fix

1. Deploy frontend only.
2. Confirm approved layout loads unchanged.
3. Confirm sidebar, columns, fonts, colors, and spacing are preserved.
4. Submit a command from the main command box.
5. Confirm POST goes to https://executive-engine-os.onrender.com/run.
6. Confirm user message appears as compact right-side bubble.
7. Confirm assistant response appears as left-side structured workflow card.
8. Confirm assistant card shows clear answer.
9. Confirm assistant card shows next action.
10. Confirm assistant card shows suggested follow-up/Continue button.
11. Confirm /run fields render compactly in order: NEXT MOVE, DECISION, ACTION STEPS, READY ASSETS, RISK, PRIORITY, RECOMMENDED COMMAND.
12. Confirm saved workflow preview appears for decision/action/asset.
13. Click Continue and confirm follow-up input is populated.
14. Submit follow-up and confirm same thread continues.
15. Click Decisions and confirm runtime decision history appears.
16. Click Action Workspace and confirm runtime tasks appear.
17. Click Ready Assets and confirm runtime assets appear.
18. Click Risk Monitor and confirm runtime risks appear.
19. Click Context and confirm latest command/objective/thread context appears.
20. Confirm Executive Summary updates from latest response.
21. Confirm Executive Intelligence shows current focus, active risk, recommended next move, and follow-up prompt.
22. Confirm backend was not changed.
23. Confirm API URL was not changed.
24. Confirm /run contract was not changed.
