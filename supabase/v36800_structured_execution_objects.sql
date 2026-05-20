-- Executive Engine OS — V36800 Structured Execution Object Engine
-- Additive Supabase schema. Does not drop or alter existing tables.

create table if not exists ee_execution_objects (
  id uuid primary key default gen_random_uuid(),
  workspace_id text not null default 'default',
  user_id text not null default 'will',
  object_type text not null,
  title text not null,
  status text not null default 'generated',
  payload jsonb not null default '{}'::jsonb,
  source_command text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists ee_active_projects (
  id uuid primary key default gen_random_uuid(),
  workspace_id text not null default 'default',
  user_id text not null default 'will',
  title text not null,
  status text not null default 'active',
  pressure_level text,
  revenue_relevance text,
  next_action text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists ee_decisions (
  id uuid primary key default gen_random_uuid(),
  workspace_id text not null default 'default',
  user_id text not null default 'will',
  decision text not null,
  rationale text,
  status text not null default 'active',
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists ee_follow_ups (
  id uuid primary key default gen_random_uuid(),
  workspace_id text not null default 'default',
  user_id text not null default 'will',
  title text not null,
  status text not null default 'open',
  due_at timestamptz,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists ee_revenue_lanes (
  id uuid primary key default gen_random_uuid(),
  workspace_id text not null default 'default',
  user_id text not null default 'will',
  title text not null,
  stage text,
  estimated_value numeric,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_ee_execution_objects_workspace on ee_execution_objects(workspace_id, user_id, object_type, status);
create index if not exists idx_ee_active_projects_workspace on ee_active_projects(workspace_id, user_id, status);
create index if not exists idx_ee_follow_ups_workspace on ee_follow_ups(workspace_id, user_id, status);
create index if not exists idx_ee_revenue_lanes_workspace on ee_revenue_lanes(workspace_id, user_id, stage);
