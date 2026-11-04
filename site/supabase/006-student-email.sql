-- Lets a teacher look up a student's sign-in email (for notifications). Run ONCE in the Supabase SQL editor. Safe to re-run.
-- Emails live in auth.users, which the API cannot read; this exposes only the one address, and only to teachers.
create or replace function public.student_email(student uuid) returns text
language sql stable security definer set search_path = '' as $$
  select u.email::text from auth.users u where u.id = student and public.is_teacher();
$$;
revoke all on function public.student_email(uuid) from public, anon;
grant execute on function public.student_email(uuid) to authenticated;
