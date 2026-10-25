-- Run once in the Supabase SQL editor.

create table public.profiles (
  id uuid primary key references auth.users on delete cascade,
  full_name text not null default '',
  role text not null default 'student' check (role in ('student', 'teacher')),
  created_at timestamptz not null default now()
);

create table public.lessons (
  id int primary key,                 -- lesson number 1..15
  title text not null,
  held_on date
);

create table public.assignments (
  id serial primary key,
  lesson_id int references public.lessons(id),
  kind text not null default 'homework' check (kind in ('homework', 'project')),
  title text not null,
  due_at timestamptz,
  weight numeric not null default 1   -- relative weight inside its category
);

create table public.submissions (
  id serial primary key,
  assignment_id int not null references public.assignments(id) on delete cascade,
  student_id uuid not null references public.profiles(id) on delete cascade,
  repo_url text,                      -- GitHub / GitLab link
  screenshot_path text,               -- path in the 'submissions' storage bucket
  file_path text,                     -- optional extra file (zip, py, ipynb...) in the same bucket
  notes text,
  submitted_at timestamptz not null default now(),
  grade numeric check (grade between 0 and 100),
  feedback text,
  graded_at timestamptz,
  unique (assignment_id, student_id)
);

create table public.attendance (
  lesson_id int not null references public.lessons(id) on delete cascade,
  student_id uuid not null references public.profiles(id) on delete cascade,
  status text not null default 'present' check (status in ('present', 'late', 'absent', 'excused')),
  primary key (lesson_id, student_id)
);

-- Final-grade weights, editable by the teacher.
create table public.grade_weights (
  category text primary key check (category in ('exam', 'homework', 'project')),
  weight numeric not null check (weight >= 0)
);
insert into public.grade_weights values ('exam', 55), ('homework', 15), ('project', 30);  -- projects: 3 x 10%; attendance is not graded

-- Final exam grade, entered by the teacher.
create table public.exam_grades (
  student_id uuid primary key references public.profiles(id) on delete cascade,
  grade numeric not null check (grade between 0 and 100)
);

-- Create a profile automatically on sign-up.
create function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profiles (id, full_name)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'full_name', ''));
  return new;
end $$;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();

create function public.is_teacher() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.profiles where id = auth.uid() and role = 'teacher');
$$;

-- Row Level Security
alter table public.profiles enable row level security;
alter table public.lessons enable row level security;
alter table public.assignments enable row level security;
alter table public.submissions enable row level security;
alter table public.attendance enable row level security;
alter table public.grade_weights enable row level security;
alter table public.exam_grades enable row level security;

create policy "own profile or teacher" on public.profiles for select
  using (id = auth.uid() or public.is_teacher());
create policy "update own name" on public.profiles for update
  using (id = auth.uid()) with check (id = auth.uid() and role = 'student');
create policy "teacher manages profiles" on public.profiles for all
  using (public.is_teacher()) with check (public.is_teacher());

create policy "read lessons" on public.lessons for select using (auth.uid() is not null);
create policy "teacher edits lessons" on public.lessons for all
  using (public.is_teacher()) with check (public.is_teacher());

create policy "read assignments" on public.assignments for select using (auth.uid() is not null);
create policy "teacher edits assignments" on public.assignments for all
  using (public.is_teacher()) with check (public.is_teacher());

create policy "read own submissions" on public.submissions for select
  using (student_id = auth.uid() or public.is_teacher());
create policy "insert own submission" on public.submissions for insert
  with check (student_id = auth.uid() and grade is null);
create policy "resubmit until graded" on public.submissions for update
  using (student_id = auth.uid() and graded_at is null)
  with check (student_id = auth.uid() and grade is null and graded_at is null and feedback is null);
create policy "teacher grades" on public.submissions for update
  using (public.is_teacher()) with check (public.is_teacher());

create policy "read own attendance" on public.attendance for select
  using (student_id = auth.uid() or public.is_teacher());
create policy "teacher edits attendance" on public.attendance for all
  using (public.is_teacher()) with check (public.is_teacher());

create policy "read own exam grade" on public.exam_grades for select
  using (student_id = auth.uid() or public.is_teacher());
create policy "teacher edits exam grades" on public.exam_grades for all
  using (public.is_teacher()) with check (public.is_teacher());

create policy "read weights" on public.grade_weights for select using (auth.uid() is not null);
create policy "teacher edits weights" on public.grade_weights for all
  using (public.is_teacher()) with check (public.is_teacher());

-- Private storage for screenshots and files: <student id>/<assignment id>/<file>
insert into storage.buckets (id, name, public) values ('submissions', 'submissions', false)
  on conflict (id) do nothing;

create policy "students upload to own folder" on storage.objects for insert to authenticated
  with check (bucket_id = 'submissions' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "students read own files" on storage.objects for select to authenticated
  using (bucket_id = 'submissions' and ((storage.foldername(name))[1] = auth.uid()::text or public.is_teacher()));

-- Make yourself the teacher after signing up once:
--   update public.profiles set role = 'teacher' where id = '<your auth user id>';
