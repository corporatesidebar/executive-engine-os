# V35150B Backend Test Checklist

## Backend-only verification

- [ ] ZIP contains `backend/main.py`
- [ ] ZIP contains `backend/requirements.txt`
- [ ] ZIP contains `README.md`
- [ ] ZIP contains `test-checklist.md`
- [ ] ZIP contains no frontend files

## Endpoint verification

- [ ] `GET /` returns 200
- [ ] `GET /` reports version `V35150B`
- [ ] `GET /health` returns 200
- [ ] `GET /health` reports version `V35150B`
- [ ] `GET /debug` returns 200
- [ ] `GET /debug` reports version `V35150B`
- [ ] `GET /test-report` returns browser page
- [ ] `GET /test-report-json` returns JSON report
- [ ] `POST /run` returns 200

## /run output contract

- [ ] `next_move` present
- [ ] `decision` present
- [ ] `action_steps` present and array
- [ ] `ready_assets` present and array
- [ ] `risk` present
- [ ] `priority` present and is `High`, `Medium`, or `Low`
- [ ] `recommended_command` present

## Test page tools

- [ ] `/test-report` has Run Tests button
- [ ] `/test-report` has Copy JSON button
- [ ] PASS / FAIL results display clearly
- [ ] Raw JSON output displays clearly

## Do-not-touch checks

- [ ] Frontend not changed
- [ ] Supabase not changed
- [ ] DB schema not changed
- [ ] API URL unchanged
- [ ] Provider routing remains OpenAI-first
