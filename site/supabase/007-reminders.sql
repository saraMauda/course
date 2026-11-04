-- Automatic reminder emails: remembers what was already sent. Run ONCE in the Supabase SQL editor. Safe to re-run.
-- Only the server (service role key) touches this table; no policies means no access for students or the anon key.
create table if not exists public.reminder_log (
  student_id uuid not null references public.profiles(id) on delete cascade,
  kind text not null,
  ref_id int not null,            -- the assignment or lesson the reminder was about
  sent_at timestamptz not null default now(),
  primary key (student_id, kind, ref_id)
);
alter table public.reminder_log enable row level security;
