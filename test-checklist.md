# V35140 Frontend Runtime Test Checklist

## Runtime Controls
- [ ] Command input allows typing
- [ ] Enter key submits command
- [ ] Execute button submits command
- [ ] Loading state appears while waiting
- [ ] Error state appears on failed request
- [ ] Follow-up input submits command
- [ ] Command chips populate command input
- [ ] Sidebar nav switches visible sections or scrolls/focuses sections

## Backend Contract
- [ ] POST goes to `https://executive-engine-os.onrender.com/run`
- [ ] Backend returns HTTP 200
- [ ] No backend files included
- [ ] API URL unchanged
- [ ] `/run` contract unchanged

## Output Rendering Order
- [ ] NEXT MOVE
- [ ] DECISION
- [ ] ACTION STEPS
- [ ] READY ASSETS
- [ ] RISK
- [ ] PRIORITY
- [ ] RECOMMENDED COMMAND

## Dynamic Panels
- [ ] Executive Summary updates from latest response
- [ ] Executive Intelligence updates from latest response
- [ ] Ready Assets section updates
- [ ] Active Risks section updates
- [ ] Tomorrow / Upcoming updates from recommended command

## Visual Scope
- [ ] Dark sidebar preserved
- [ ] White workspace preserved
- [ ] Three-column desktop layout preserved
- [ ] Orange action button preserved
- [ ] No generic chatbot redesign
