create table if not exists items (
  id uuid primary key default gen_random_uuid(),
  input text,
  mode text,
  decision text,
  next_move text,
  actions jsonb,
  risk text,
  priority text,
  created_at timestamp with time zone default now()
);

alter table items enable row level security;

create policy "Allow API access"
on items
for all
using (true)
with check (true);
