# V35140 Frontend Interactivity Test Checklist

## Must Pass
- [ ] Frontend loads visually.
- [ ] Command input allows typing.
- [ ] Clear button clears the command input.
- [ ] Execute button is clickable.
- [ ] Execute button sends POST request to https://executive-engine-os.onrender.com/run.
- [ ] POST /run returns 200 from locked backend.
- [ ] Response renders in this order:
  1. NEXT MOVE
  2. DECISION
  3. ACTION STEPS
  4. READY ASSETS
  5. RISK
  6. PRIORITY
  7. RECOMMENDED COMMAND
- [ ] Sidebar items are clickable and switch active state.
- [ ] Suggested command chips are clickable and populate the input.
- [ ] Follow-up input accepts typing.
- [ ] No console JavaScript errors.
- [ ] No CORS errors.

## Not Touched
- [ ] Backend unchanged.
- [ ] API URL unchanged.
- [ ] /run contract unchanged.
- [ ] Supabase unchanged.
- [ ] DB schema unchanged.
- [ ] Provider routing unchanged.
- [ ] Approved layout structure preserved.
