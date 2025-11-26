create extension if not exists pgcrypto;

create table if not exists events (
  id uuid primary key default gen_random_uuid(),

  interview_id uuid not null,
  candidate_user_id uuid null,
  task_id text null,

  source text not null,
  type text not null,
  ts timestamptz not null,
  payload jsonb not null default '{}'::jsonb,

  created_at timestamptz not null default now()
);

create index if not exists idx_events_interview_ts on events (interview_id, ts);
create index if not exists idx_events_interview_task_ts on events (interview_id, task_id, ts);
create index if not exists idx_events_type on events (type);
