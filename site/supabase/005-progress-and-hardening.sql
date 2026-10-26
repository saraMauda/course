-- Lesson progress + submission timestamp hardening. Run ONCE in the Supabase SQL editor. Safe to re-run.

-- 1. Lessons a student marked as completed ---------------------------------------------------------
create table if not exists public.lesson_progress (
  student_id uuid not null references public.profiles(id) on delete cascade,
  lesson_id int not null references public.lessons(id) on delete cascade,
  completed_at timestamptz not null default now(),
  primary key (student_id, lesson_id)
);
alter table public.lesson_progress enable row level security;

drop policy if exists "read own progress" on public.lesson_progress;
create policy "read own progress" on public.lesson_progress for select
  using (student_id = auth.uid() or public.is_teacher());
drop policy if exists "mark own progress" on public.lesson_progress;
create policy "mark own progress" on public.lesson_progress for insert
  with check (student_id = auth.uid() and public.is_approved());
drop policy if exists "unmark own progress" on public.lesson_progress;
create policy "unmark own progress" on public.lesson_progress for delete
  using (student_id = auth.uid());

-- 2. submitted_at is set by the server --------------------------------------------------------------
-- Otherwise a student could send a back-dated timestamp and dodge the "late" flag.
create or replace function public.stamp_submission() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if not public.is_teacher() then
    if tg_op = 'INSERT' then
      new.submitted_at := now();
    elsif new.repo_url is distinct from old.repo_url
       or new.screenshot_path is distinct from old.screenshot_path
       or new.file_path is distinct from old.file_path
       or new.items is distinct from old.items
       or new.notes is distinct from old.notes then
      new.submitted_at := now();
    else
      new.submitted_at := old.submitted_at;
    end if;
  end if;
  return new;
end $$;

drop trigger if exists stamp_submission on public.submissions;
create trigger stamp_submission before insert or update on public.submissions
  for each row execute function public.stamp_submission();
