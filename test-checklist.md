# V35140 Approved Layout Runtime Fix — Frontend Test Checklist

## Package
- [ ] ZIP contains `frontend/index.html`
- [ ] ZIP contains `README.md`
- [ ] ZIP contains `test-checklist.md`
- [ ] ZIP contains no backend files

## Visual Layout
- [ ] Dark left sidebar matches approved screenshot structure
- [ ] White main workspace preserved
- [ ] Three-column layout preserved
- [ ] Large center workflow/chat area preserved
- [ ] Executive Summary middle column preserved
- [ ] Executive Intelligence right column preserved
- [ ] Original spacing/card density preserved
- [ ] Orange Execute button preserved

## Runtime Functionality
- [ ] Command input allows typing
- [ ] Enter submits command
- [ ] Execute button submits command
- [ ] POST goes to `https://executive-engine-os.onrender.com/run`
- [ ] Loading state appears while waiting
- [ ] Error state appears if request fails
- [ ] Sidebar clicks update active state and focus relevant area
- [ ] Command chips populate input
- [ ] Follow-up input submits
- [ ] Executive Summary updates from latest `/run` response
- [ ] Right intelligence panel updates from latest `/run` response/context

## Output Order
- [ ] NEXT MOVE
- [ ] DECISION
- [ ] ACTION STEPS
- [ ] READY ASSETS
- [ ] RISK
- [ ] PRIORITY
- [ ] RECOMMENDED COMMAND

## Scope Guardrails
- [ ] Backend untouched
- [ ] API URL unchanged
- [ ] `/run` contract unchanged
- [ ] Supabase/DB untouched
- [ ] Provider routing untouched
