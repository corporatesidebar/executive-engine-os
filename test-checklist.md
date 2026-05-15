# V35140 Real Runtime Controller Test Checklist

## Visual Lock
- [ ] Dark left sidebar preserved
- [ ] White workspace preserved
- [ ] Original three-column layout preserved
- [ ] Large center workflow/chat area preserved
- [ ] Executive Summary middle column preserved
- [ ] Executive Intelligence right column preserved
- [ ] Orange Execute button preserved
- [ ] Premium SaaS spacing/card density preserved

## Runtime Behavior
- [ ] Command input accepts typing
- [ ] Enter submits command
- [ ] Execute button submits command
- [ ] POST goes to `https://executive-engine-os.onrender.com/run`
- [ ] Loading state appears while waiting
- [ ] Success state appears after successful response
- [ ] Error state appears on failed response
- [ ] Response appends to workflow/chat area
- [ ] Output renders in this order:
  1. NEXT MOVE
  2. DECISION
  3. ACTION STEPS
  4. READY ASSETS
  5. RISK
  6. PRIORITY
  7. RECOMMENDED COMMAND
- [ ] Follow-up input submits and appends/updates workflow
- [ ] Sidebar nav switches real sections/states
- [ ] Command chips populate command input
- [ ] Command chip double-click runs the command
- [ ] Executive Summary updates from latest `/run` response
- [ ] Executive Intelligence updates from current response/context

## Guardrails
- [ ] No backend files included
- [ ] API URL unchanged
- [ ] `/run` contract unchanged
- [ ] Supabase untouched
- [ ] DB schema untouched
- [ ] Provider routing untouched
