-- Run ONCE if you already ran schema.sql before the exam grade was added.
-- Weights: exam 55%, homework 15%, projects 30% (3 x 10%). Attendance is not part of the grade.
delete from public.grade_weights where category = 'attendance';
alter table public.grade_weights drop constraint grade_weights_category_check;
alter table public.grade_weights add constraint grade_weights_category_check
  check (category in ('exam', 'homework', 'project'));
insert into public.grade_weights values ('exam', 55), ('homework', 15), ('project', 30)
  on conflict (category) do update set weight = excluded.weight;

create table public.exam_grades (
  student_id uuid primary key references public.profiles(id) on delete cascade,
  grade numeric not null check (grade between 0 and 100)
);
alter table public.exam_grades enable row level security;
create policy "read own exam grade" on public.exam_grades for select
  using (student_id = auth.uid() or public.is_teacher());
create policy "teacher edits exam grades" on public.exam_grades for all
  using (public.is_teacher()) with check (public.is_teacher());
