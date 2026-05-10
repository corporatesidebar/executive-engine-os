# Executive Engine OS — V36330 Clean Stable Recovery Baseline

## Backend Origin
This is a clean recovery baseline created from the recovery requirements. It is not confirmed as the original V35060 backend source code.

Reason: the verified V35060 source package was not available in this session, so this baseline was rebuilt to match the required stable behavior and required endpoint contract.

## Frontend API URL
The frontend is configured to call:

https://executive-engine-os.onrender.com

If the live backend URL changes, update `API_BASE` in `/frontend/index.html`.

## Included Files

/frontend/index.html  
/backend/main.py  
/backend/requirements.txt  
README.md

## Required Backend Tests

GET /  
GET /health  
GET /debug  
POST /run  

## Required Frontend Tests

- Frontend loads
- Frontend connects to backend
- Command sends POST request to /run
- Structured response displays in this order:
  1. NEXT MOVE
  2. DECISION
  3. ACTION STEPS
  4. RISK
  5. PRIORITY
- Clear loading state
- Clear error state

## Deployment Instructions — Render

### Backend
1. Upload repo files to GitHub.
2. Create or update Render Web Service.
3. Root directory: `backend`
4. Start command:
   `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variable:
   `OPENAI_API_KEY`
6. Optional:
   `CLAUDE_API_KEY`
7. Deploy latest commit.

### Frontend
1. Create or update Render Static Site.
2. Root directory: `frontend`
3. Publish directory: `.`
4. Deploy latest commit.

## Known Limitations

- This is a recovery baseline, not a feature build.
- No Supabase changes.
- No memory expansion.
- No advanced workflow modules.
- Claude cannot break `/run`; OpenAI-first/fallback logic is used.
- If no API key is available, `/run` returns a valid fallback JSON response.

## Stability Rule

This version is stable only if POST /run returns valid JSON in the required shape and the frontend displays the structured response.
