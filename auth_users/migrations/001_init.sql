create extension if not exists pgcrypto;

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  password_hash text null,
  name text not null,
  role text not null check (role in ('hr', 'candidate')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists users_email_idx on users (email);
