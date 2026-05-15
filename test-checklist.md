# V35140 Layout Lock Runtime Restore — Test Checklist

## Visual layout
- [ ] Dark left sidebar preserved
- [ ] White main workspace preserved
- [ ] Original three-column layout preserved
- [ ] Large center workflow/chat area preserved
- [ ] Middle Executive Summary cards preserved
- [ ] Right Executive Intelligence panel preserved
- [ ] Orange Execute button preserved
- [ ] Blue/orange/navy brand direction preserved

## Runtime behavior
- [ ] Command input allows typing
- [ ] Enter submits command
- [ ] Execute button submits command
- [ ] POST goes to `https://executive-engine-os.onrender.com/run`
- [ ] Loading state appears while waiting
- [ ] Error state appears on failed request
- [ ] Sidebar clicks switch active state and focus relevant area
- [ ] Command chips populate command input
- [ ] Follow-up input submits with Enter
- [ ] Follow-up send icon submits
- [ ] Executive Summary updates from latest response
- [ ] Executive Intelligence updates from latest response/context

## Output order
- [ ] NEXT MOVE
- [ ] DECISION
- [ ] ACTION STEPS
- [ ] READY ASSETS
- [ ] RISK
- [ ] PRIORITY
- [ ] RECOMMENDED COMMAND

## Non-touched areas
- [ ] No backend files included
- [ ] No API URL change
- [ ] No `/run` contract change
- [ ] No Supabase or DB changes
- [ ] No provider routing changes
