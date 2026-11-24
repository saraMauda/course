-- Lesson recording: a Google Drive link per lesson, entered by the teacher at /admin/lessons.
-- Run ONCE in the Supabase SQL editor. Safe to re-run.
-- No new policies: "teacher edits lessons" already covers writing, "read lessons" (approved users) covers reading.
alter table public.lessons add column if not exists video_url text;

alter table public.lessons drop constraint if exists lessons_video_url_drive;
alter table public.lessons add constraint lessons_video_url_drive
  check (video_url is null or video_url like 'https://drive.google.com/%');
