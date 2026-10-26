-- Per-item project submissions. Run ONCE in the Supabase SQL editor. Safe to re-run.

-- What the student attached for each checklist item: { "<item key>": { "text": "...", "path": "<storage path>" } }
alter table public.submissions add column if not exists items jsonb not null default '{}'::jsonb;

-- The teacher's tick for each item. Students can read theirs but never write.
create table if not exists public.submission_checks (
  submission_id int not null references public.submissions(id) on delete cascade,
  item_key text not null,
  ok boolean not null default true,
  primary key (submission_id, item_key)
);
alter table public.submission_checks enable row level security;

drop policy if exists "read own checks" on public.submission_checks;
create policy "read own checks" on public.submission_checks for select
  using (public.is_teacher() or exists (
    select 1 from public.submissions s where s.id = submission_id and s.student_id = auth.uid()));
drop policy if exists "teacher edits checks" on public.submission_checks;
create policy "teacher edits checks" on public.submission_checks for all
  using (public.is_teacher()) with check (public.is_teacher());
