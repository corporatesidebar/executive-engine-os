-- Executive Engine OS V94 Supabase Schema Additions
-- Run after V92 schema exists.
-- This keeps V92 tables and adds optional execution loop tracking.

create table if not exists public.execution_loops (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references public.users(id) on delete cascade,
  run_id uuid references public.runs(id) on delete set null,
  current_focus text,
  next_action text,
  next_prompt text,
  status text not null default 'open',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_execution_loops_user_status on public.execution_loops(user_id, status);
alter table if exists public.execution_loops enable row level security;

select
  schemaname,
  tablename,
  rowsecurity as rls_enabled
from pg_tables
where schemaname = 'public'
order by tablename;
