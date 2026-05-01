-- Executive Engine OS V92.2 Supabase Schema + Security Lock
-- Architecture: Frontend -> Render Backend -> Supabase service role key.
-- Never expose SUPABASE_SERVICE_ROLE_KEY in frontend.

create extension if not exists "uuid-ossp";

alter table if exists public.items enable row level security;

create table if not exists public.users (
  id uuid primary key default uuid_generate_v4(),
  external_user_id text unique,
  email text,
  display_name text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.profiles (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references public.users(id) on delete cascade unique,
  role text,
  goals text,
  experience text,
  constraints text,
  resume_context text,
  preferences jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.runs (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references public.users(id) on delete cascade,
  session_id text,
  mode text not null default 'execution',
  depth text not null default 'standard',
  input text not null,
  context text,
  output jsonb not null default '{}'::jsonb,
  model text,
  latency_ms integer,
  status text not null default 'completed',
  created_at timestamptz not null default now()
);

create table if not exists public.actions (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references public.users(id) on delete cascade,
  run_id uuid references public.runs(id) on delete set null,
  text text not null,
  priority text default 'medium',
  status text not null default 'open',
  owner text,
  due_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.decisions (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references public.users(id) on delete cascade,
  run_id uuid references public.runs(id) on delete set null,
  decision text not null,
  risk text,
  priority text default 'medium',
  rationale text,
  next_move text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.memory_items (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references public.users(id) on delete cascade,
  type text not null,
  content text not null,
  importance integer not null default 3 check (importance between 1 and 5),
  source_run_id uuid references public.runs(id) on delete set null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.learning_events (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references public.users(id) on delete cascade,
  event_type text not null,
  mode text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.aggregate_insights (
  id uuid primary key default uuid_generate_v4(),
  insight_type text not null,
  summary text not null,
  count integer not null default 1,
  metadata jsonb not null default '{}'::jsonb,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now()
);

create table if not exists public.automation_plans (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references public.users(id) on delete cascade,
  run_id uuid references public.runs(id) on delete set null,
  title text not null,
  description text,
  target_service text,
  status text not null default 'planned',
  required_credentials jsonb not null default '[]'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_runs_user_created_at on public.runs(user_id, created_at desc);
create index if not exists idx_actions_user_status on public.actions(user_id, status);
create index if not exists idx_decisions_user_created_at on public.decisions(user_id, created_at desc);
create index if not exists idx_memory_user_type on public.memory_items(user_id, type);
create index if not exists idx_learning_events_user_created_at on public.learning_events(user_id, created_at desc);

alter table if exists public.items enable row level security;
alter table if exists public.users enable row level security;
alter table if exists public.profiles enable row level security;
alter table if exists public.runs enable row level security;
alter table if exists public.actions enable row level security;
alter table if exists public.decisions enable row level security;
alter table if exists public.memory_items enable row level security;
alter table if exists public.learning_events enable row level security;
alter table if exists public.aggregate_insights enable row level security;
alter table if exists public.automation_plans enable row level security;

select
  schemaname,
  tablename,
  rowsecurity as rls_enabled
from pg_tables
where schemaname = 'public'
order by tablename;
