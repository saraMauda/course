-- Teacher tools: custom email templates, a log of emails sent from the site, and bulk email lookup.
-- Run ONCE in the Supabase SQL editor. Safe to re-run.

-- 1. Email templates the teacher writes herself. Placeholders look like {{שם}} and are filled per student when sending.
create table if not exists public.email_templates (
  id serial primary key,
  name text not null,
  subject text not null,
  body text not null,
  created_at timestamptz not null default now()
);
alter table public.email_templates enable row level security;
drop policy if exists "teacher manages templates" on public.email_templates;
create policy "teacher manages templates" on public.email_templates for all
  using (public.is_teacher()) with check (public.is_teacher());

-- 2. What was sent to whom (the rendered text, so it reads exactly as the student saw it).
create table if not exists public.email_log (
  id bigserial primary key,
  student_id uuid references public.profiles(id) on delete set null,
  subject text not null,
  body text not null,
  status text not null check (status in ('sent', 'failed')),
  sent_at timestamptz not null default now()
);
alter table public.email_log enable row level security;
drop policy if exists "teacher reads email log" on public.email_log;
create policy "teacher reads email log" on public.email_log for select using (public.is_teacher());
drop policy if exists "teacher writes email log" on public.email_log;
create policy "teacher writes email log" on public.email_log for insert with check (public.is_teacher());

-- 3. Sign-in emails for several students at once (they live in auth.users, which the API cannot read).
-- Returns nothing unless the caller is a teacher.
create or replace function public.student_emails(ids uuid[]) returns table (id uuid, email text)
language sql stable security definer set search_path = '' as $$
  select u.id, u.email::text from auth.users u where u.id = any(ids) and public.is_teacher();
$$;
revoke all on function public.student_emails(uuid[]) from public, anon;
grant execute on function public.student_emails(uuid[]) to authenticated;
