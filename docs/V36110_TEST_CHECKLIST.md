
# V36110 Test Checklist

Backend:
- [ ] /health
- [ ] /test-report-json
- [ ] /profile-state
- [ ] POST /profile-setup
- [ ] POST /profile-aware-flow

Frontend:
- [ ] Profile Setup appears in nav
- [ ] Save Context Profile works
- [ ] Profile-Aware Flow works
- [ ] Outputs reference profile context

Macro test:
1. Save profile:
   Role: COO
   Company: mid-sized services company
   Priorities: sales conversion, client follow-up, team accountability
   Risks: delayed proposals, unclear ownership
2. Run: I have too many priorities today.
3. Confirm output references priorities/risks.
