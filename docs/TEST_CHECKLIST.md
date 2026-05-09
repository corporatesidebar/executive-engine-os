# V36030 Test Checklist

## Backend

- [ ] `/health` returns online
- [ ] `/debug` returns version and config status
- [ ] `/providers` returns provider config
- [ ] `/test-report-json` returns pass/warn checks
- [ ] `/run` returns structured output
- [ ] `/db-status` works if present
- [ ] `/demo-state` works if present
- [ ] `/operating-layer-state` works if present
- [ ] `/daily-use-state` works if present
- [ ] `/how-to-use` works if present

## Frontend

- [ ] Frontend loads
- [ ] Existing navigation works
- [ ] Today page works
- [ ] Daily Use page works
- [ ] Operating Layer page works
- [ ] Run Command works
- [ ] Action Queue works
- [ ] Assets page still displays
- [ ] Database/system status still displays
- [ ] No major layout break

## Macro test

Use:

```text
I have client follow-ups, a proposal to prepare, meetings coming up, and too many priorities. Tell me what to do first today.
```

Expected:

- clear first move
- useful top 3
- follow-up suggestion
- asset to create
- risk
- end-of-day review

## Classification

- PROMOTE if cleanup deploys and core system still works
- FIX if minor UI or route issue
- ROLLBACK if `/run` or frontend fails
