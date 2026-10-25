-- Security hardening. Run ONCE in the Supabase SQL editor, after schema.sql (and 002-add-exam.sql if you ran an older schema).
-- Safe to re-run.

-- 1. Registration approval -------------------------------------------------------------------------
alter table public.profiles add column if not exists approved boolean not null default false;

-- Everyone who already has an account stays in (you can un-approve later). New sign-ups start unapproved.
update public.profiles set approved = true where approved = false;
update public.profiles set approved = true where role = 'teacher';

create or replace function public.is_approved() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.profiles
    where id = auth.uid() and (approved or role = 'teacher')
  );
$$;

-- Only a teacher can approve; callable through supabase.rpc('approve_student', ...)
create or replace function public.approve_student(student uuid, ok boolean default true) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if not public.is_teacher() then
    raise exception 'not allowed';
  end if;
  update public.profiles set approved = ok where id = student and role = 'student';
end $$;
revoke all on function public.approve_student(uuid, boolean) from public, anon;
grant execute on function public.approve_student(uuid, boolean) to authenticated;

-- 2. Nobody can promote or approve themselves ------------------------------------------------------
-- Signed-in users may edit only their own full_name. role/approved change only through approve_student()
-- or directly in the SQL editor.
revoke update on public.profiles from anon, authenticated;
grant update (full_name) on public.profiles to authenticated;

drop policy if exists "update own name" on public.profiles;
drop policy if exists "teacher manages profiles" on public.profiles;
create policy "update own name" on public.profiles for update
  using (id = auth.uid()) with check (id = auth.uid());

-- Anonymous visitors get no direct table access at all.
revoke all on all tables in schema public from anon;
revoke all on all sequences in schema public from anon;

-- 3. Only approved users can read course data or submit --------------------------------------------
drop policy if exists "read lessons" on public.lessons;
create policy "read lessons" on public.lessons for select using (public.is_approved());

drop policy if exists "read assignments" on public.assignments;
create policy "read assignments" on public.assignments for select using (public.is_approved());

drop policy if exists "read weights" on public.grade_weights;
create policy "read weights" on public.grade_weights for select using (public.is_approved());

drop policy if exists "insert own submission" on public.submissions;
create policy "insert own submission" on public.submissions for insert
  with check (
    student_id = auth.uid() and public.is_approved()
    and grade is null and graded_at is null and feedback is null
  );

drop policy if exists "resubmit until graded" on public.submissions;
create policy "resubmit until graded" on public.submissions for update
  using (student_id = auth.uid() and graded_at is null and public.is_approved())
  with check (student_id = auth.uid() and grade is null and graded_at is null and feedback is null);

drop policy if exists "students upload to own folder" on storage.objects;
create policy "students upload to own folder" on storage.objects for insert to authenticated
  with check (
    bucket_id = 'submissions'
    and (storage.foldername(name))[1] = auth.uid()::text
    and public.is_approved()
  );

-- 10 MB cap per uploaded file
update storage.buckets set file_size_limit = 10485760 where id = 'submissions';

-- 4. Put role + approval inside the JWT ------------------------------------------------------------
-- After running this, enable it in the dashboard:
--   Authentication -> Hooks -> Custom Access Token -> select public.custom_access_token_hook
-- The site reads the claims `user_role` and `approved` from the verified JWT. Without the hook the site
-- falls back to one small database lookup, so nothing breaks if you forget.
create or replace function public.custom_access_token_hook(event jsonb) returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare
  claims jsonb := event -> 'claims';
  p record;
begin
  select role, approved into p from public.profiles where id = (event ->> 'user_id')::uuid;
  claims := jsonb_set(claims, '{user_role}', to_jsonb(coalesce(p.role, 'student')));
  claims := jsonb_set(claims, '{approved}', to_jsonb(coalesce(p.approved, false) or coalesce(p.role, '') = 'teacher'));
  return jsonb_set(event, '{claims}', claims);
end $$;

grant execute on function public.custom_access_token_hook(jsonb) to supabase_auth_admin;
revoke execute on function public.custom_access_token_hook(jsonb) from authenticated, anon, public;
