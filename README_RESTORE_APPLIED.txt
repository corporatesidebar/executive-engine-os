V35080 Restore Applied

This package was rebuilt from the uploaded GitHub ZIP.

Applied fix:
- backend/main.py provider_plan now uses OpenAI first by default.
- Auto mode returns ["openai", "claude"].
- Explicit Claude returns ["claude", "openai"] so Claude failure falls back safely.
- Explicit OpenAI returns ["openai"].

No frontend redesign applied.
No Supabase schema changes applied.
No OAuth activation applied.
No route removals applied.
