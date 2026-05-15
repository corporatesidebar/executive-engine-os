# V35140 Frontend Workflow Rendering Test Checklist

## Package Inspection
- [ ] ZIP contains `frontend/index.html`
- [ ] ZIP contains `README.md`
- [ ] ZIP contains `test-checklist.md`
- [ ] ZIP contains no backend files
- [ ] ZIP contains no Supabase or DB files

## Layout Preservation
- [ ] Approved dark sidebar is unchanged
- [ ] Header/topbar is unchanged
- [ ] Main command area is unchanged
- [ ] Executive Summary column is preserved
- [ ] Executive Intelligence column is preserved
- [ ] Fonts, colors, spacing, columns, and card structure remain visually consistent with the approved layout

## Runtime Workflow
- [ ] Main command input accepts text
- [ ] Execute button submits command
- [ ] Enter submits command from main input
- [ ] Follow-up input stays pinned at bottom of workflow panel
- [ ] Follow-up input submits on Enter
- [ ] Follow-up send icon submits
- [ ] Loading state appears while request is running
- [ ] Error state appears if request fails

## Chat Rendering
- [ ] User message appears as compact right-side bubble
- [ ] Assistant message appears as left-side structured card/bubble
- [ ] Conversation history remains readable
- [ ] Assistant output does not render as pasted/plain document content
- [ ] Vertical spacing inside assistant response is compact

## Backend Contract
- [ ] POST goes to `https://executive-engine-os.onrender.com/run`
- [ ] API URL is unchanged
- [ ] `/run` contract is unchanged
- [ ] Response renders in this order:
  - [ ] NEXT MOVE
  - [ ] DECISION
  - [ ] ACTION STEPS
  - [ ] READY ASSETS
  - [ ] RISK
  - [ ] PRIORITY
  - [ ] RECOMMENDED COMMAND

## State Panels
- [ ] Executive Summary cards update from latest response
- [ ] Executive Intelligence cards update from latest response/context
- [ ] Static fake demo conversation is removed from the runtime workflow
- [ ] No backend, provider routing, Supabase, or DB behavior changed
