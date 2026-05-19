# V35120 — Command Centre DB Experience

Major product jump.

## Frontend
- Creative command-centre cockpit experience.
- Smooth page transitions.
- Full left navigation restored.
- Separate sub-pages for each tool-belt section.
- Command Centre / ChatGPT-style execution page with history.
- Seeded test content across sections.
- Action queue with checkboxes.
- Collapsed operator rail.
- Database status and test-write page.

## Backend
- Version: 35120-command-centre-db-experience.
- Existing routes preserved.
- Optional Supabase persistence layer added.
- Safe fallback to in-memory mode if Supabase env vars are absent.
- New routes: /db-status, /db-items, /db-test-write.
- /run, /create-workspace, /save-action, /save-decision, /save-asset persist to DB when configured.

## Required Supabase env vars on Render backend
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
- SUPABASE_TABLE defaults to items

Recommended table columns: id uuid default gen_random_uuid(), kind text, payload jsonb, created_at timestamptz.
