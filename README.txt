Executive Engine OS V48

Upload:
- frontend/index.html
- backend/main.py
- backend/requirements.txt

Render backend:
- Root Directory: backend
- Build Command: pip install -r requirements.txt
- Start Command: uvicorn main:app --host 0.0.0.0 --port 10000

Render frontend:
- Root Directory: frontend
- Build Command: blank
- Publish Directory: .

Required backend env:
- OPENAI_API_KEY

Optional:
- OPENAI_MODEL=gpt-4o-mini
- ALLOWED_ORIGINS=https://executive-engine-frontend.onrender.com

V48 adds executive workflow fields:
- executive_summary
- financial_impact
- leadership_implication
- execution_score
- decision_confidence
- time_horizon
