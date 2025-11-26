create extension if not exists pgcrypto;

create table if not exists interviews (
  id uuid primary key default gen_random_uuid(),
  hr_user_id uuid not null,
  candidate_user_id uuid not null,

  topics jsonb not null default '[]'::jsonb,
  level text not null,

  planned_start timestamptz null,
  planned_end timestamptz null,
  start_time timestamptz null,
  end_time timestamptz null,

  status text not null default 'created' check (status in ('created','active','finished','canceled')),

  task_ids text[] not null default '{}',

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists interviews_hr_idx on interviews (hr_user_id, created_at desc);
create index if not exists interviews_candidate_idx on interviews (candidate_user_id);

create table if not exists interview_invites (
  id uuid primary key default gen_random_uuid(),
  interview_id uuid not null references interviews(id) on delete cascade,

  token text not null unique,
  expires_at timestamptz not null,

  created_at timestamptz not null default now(),
  revoked_at timestamptz null,

  claimed_at timestamptz null,
  claimed_by_user_id uuid null
);

create index if not exists invites_interview_idx on interview_invites (interview_id, created_at desc);
create index if not exists invites_token_idx on interview_invites (token);
