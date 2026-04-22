Replace ONLY command.html in your GitHub repo for the static site.

Why:
- Frontend is running on executive-engine-os-1.onrender.com
- Backend is running on executive-engine-os.onrender.com
- fetch("/api/command") only works when frontend and backend are on the same host
- This file changes fetch to the full backend URL:
  https://executive-engine-os.onrender.com/api/command
