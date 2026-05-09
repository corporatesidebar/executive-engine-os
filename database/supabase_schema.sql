-- Executive Engine OS V35120 Supabase persistence table
create extension if not exists pgcrypto;

create table if not exists public.items (
  id uuid primary key default gen_random_uuid(),
  kind text not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists items_kind_idx on public.items(kind);
create index if not exists items_created_at_idx on public.items(created_at desc);

-- For easiest private backend access, use SUPABASE_SERVICE_ROLE_KEY in Render.
-- Do not expose the service role key in frontend code.
