-- Executive Engine OS V121 clean schema
create extension if not exists pgcrypto;

create table if not exists public.users (
  id uuid primary key default gen_random_uuid(),
  external_user_id text unique not null,
  email text,
  display_name text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id) on delete cascade,
  role text,
  goals text,
  constraints text,
  context text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id) on delete cascade,
  input text not null,
  mode text default 'execution',
  depth text default 'standard',
  output jsonb default '{}'::jsonb,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create table if not exists public.actions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id) on delete cascade,
  run_id uuid references public.runs(id) on delete set null,
  text text not null,
  priority text default 'medium',
  status text default 'open',
  owner text,
  due_at timestamptz,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.decisions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id) on delete cascade,
  run_id uuid references public.runs(id) on delete set null,
  decision text not null,
  risk text,
  priority text default 'medium',
  rationale text,
  next_move text,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create table if not exists public.memory_items (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id) on delete cascade,
  type text default 'note',
  content text not null,
  importance integer default 3,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create index if not exists idx_runs_user_created on public.runs(user_id, created_at desc);
create index if not exists idx_actions_user_status_created on public.actions(user_id, status, created_at desc);
create index if not exists idx_decisions_user_created on public.decisions(user_id, created_at desc);
create index if not exists idx_memory_user_importance_created on public.memory_items(user_id, importance desc, created_at desc);

alter table public.users enable row level security;
alter table public.profiles enable row level security;
alter table public.runs enable row level security;
alter table public.actions enable row level security;
alter table public.decisions enable row level security;
alter table public.memory_items enable row level security;

-- Service role bypasses RLS. These policies are permissive for authenticated use if you later add auth.
do $$
begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='users' and policyname='service_all_users') then
    create policy service_all_users on public.users for all using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='profiles' and policyname='service_all_profiles') then
    create policy service_all_profiles on public.profiles for all using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='runs' and policyname='service_all_runs') then
    create policy service_all_runs on public.runs for all using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='actions' and policyname='service_all_actions') then
    create policy service_all_actions on public.actions for all using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='decisions' and policyname='service_all_decisions') then
    create policy service_all_decisions on public.decisions for all using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='memory_items' and policyname='service_all_memory_items') then
    create policy service_all_memory_items on public.memory_items for all using (true) with check (true);
  end if;
end $$;
