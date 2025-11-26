alter table users
  alter column password_hash drop not null;

alter table users
  add column if not exists updated_at timestamptz not null default now();
