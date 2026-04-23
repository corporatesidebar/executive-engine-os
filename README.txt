Executive Engine V3

Upload both folders to the existing GitHub repo: executive-engine-os

Render settings:
- Root Directory: backend
- Build Command: pip install -r requirements.txt
- Start Command: uvicorn main:app --host 0.0.0.0 --port 10000

Environment variable required:
- OPENAI_API_KEY = your real OpenAI API key
