# V35140 Runtime JavaScript Fix Test Checklist

## Frontend runtime
- [ ] Page loads visually with approved layout intact.
- [ ] Command input accepts typing.
- [ ] Pressing Enter in command input submits.
- [ ] Execute button submits.
- [ ] Clear button clears and refocuses command input.
- [ ] Command chips populate command input.
- [ ] Follow-up input accepts typing.
- [ ] Pressing Enter in follow-up input submits.
- [ ] Follow-up send icon submits.
- [ ] Sidebar nav items change active state.
- [ ] Sidebar nav items focus/scroll to relevant workspace areas.

## Backend connection
- [ ] POST request goes to https://executive-engine-os.onrender.com/run
- [ ] Request body includes command/input/message for compatibility.
- [ ] Response renders without console errors.

## Output order
- [ ] NEXT MOVE
- [ ] DECISION
- [ ] ACTION STEPS
- [ ] READY ASSETS
- [ ] RISK
- [ ] PRIORITY
- [ ] RECOMMENDED COMMAND

## Guardrails
- [ ] No backend files included.
- [ ] No DB/Supabase files included.
- [ ] No provider routing changes.
