# Test Checklist — V35140 Guided Workflow Runtime Fix

## Frontend Load
- [ ] Frontend loads without console syntax errors.
- [ ] Four-column layout remains visible at desktop width.
- [ ] Dark sidebar remains unchanged.
- [ ] Command area remains unchanged.
- [ ] Executive Summary column remains visible.
- [ ] Executive Intelligence column remains visible.

## Backend Connection
- [ ] Submit command from main command box.
- [ ] Request posts to https://executive-engine-os.onrender.com/run.
- [ ] API URL is unchanged.
- [ ] /run response contract is unchanged.

## Main Workflow
- [ ] User message appears as right-side bubble.
- [ ] Assistant response appears as left-side guided executive workflow card.
- [ ] Response starts with clear plain-English answer.
- [ ] “Do this next” appears prominently.
- [ ] Action steps appear as task-style rows.
- [ ] Ready assets appear as asset cards.
- [ ] Risk appears as warning card.
- [ ] Continue with recommended command button runs the recommended command.
- [ ] Turn into action plan button runs a follow-up action-plan command.
- [ ] Draft asset button runs a follow-up asset-drafting command.
- [ ] Save decision button updates runtime decision state.
- [ ] Follow-up input continues the same thread.

## Runtime Panels
- [ ] Sidebar sections show runtime data, not filler.
- [ ] Decisions shows captured decisions.
- [ ] Meeting Prep / Action Workspace shows task rows.
- [ ] Files / Ready Assets shows assets.
- [ ] Risk Monitor shows risks.
- [ ] Context shows latest command, recommendation, and thread count.
- [ ] Executive Summary explains current operating state.
- [ ] Executive Intelligence explains current focus, active risk, next move, and follow-up.

## Guardrails
- [ ] No backend files included.
- [ ] No Supabase files included.
- [ ] No DB changes included.
- [ ] No provider-routing changes included.
