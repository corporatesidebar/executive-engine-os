services:
  - type: web
    name: executive-engine-os
    env: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT

  - type: static
    name: executive-engine-frontend
    rootDir: frontend
    buildCommand: ""
    staticPublishPath: .
