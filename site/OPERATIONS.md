# Operations

## Supabase setup order
Run in the SQL editor, once each (all are safe to re-run):
1. `supabase/schema.sql` (+ `seed.sql`)
2. `supabase/002-add-exam.sql`, `003-security.sql`, `004-project-items.sql`
3. `supabase/005-progress-and-hardening.sql` (lesson progress, server-side `submitted_at`)
4. Authentication → Hooks → Custom Access Token → `public.custom_access_token_hook`

## Backups and restore
- Supabase free tier has **no automatic backups**. Pro includes daily backups (7 days).
- Manual backup (run monthly and before every term ends):
  ```bash
  supabase db dump --db-url "$SUPABASE_DB_URL" -f backup-$(date +%F).sql
  ```
  The connection string is in Project Settings → Database. Keep the file outside the repo (it contains student data).
- Uploaded files live in the private `submissions` bucket; download them from Storage if you need a copy (the SQL dump does not include them).
- Restore: create a new project, run `psql "$NEW_DB_URL" -f backup-YYYY-MM-DD.sql`, then re-create the storage bucket and hook (step 4).
- Quick copy for the teacher: `/admin` → ייצוא ציונים / ייצוא נוכחות (CSV).

## Security checklist (reviewed)
- Students can read only their own rows (submissions, attendance, exam grade, progress, checks); teachers read all (`is_teacher()`).
- Students cannot write grades, feedback, attendance, approval or role: no policy allows it, and `profiles` is column-restricted to `full_name`.
- `submitted_at` is set by a DB trigger (005), so the "late" flag cannot be faked.
- Storage: students upload only under their own `<user id>/` folder; reads are limited to the owner and teachers; 10 MB cap per file.
- Everything except `/`, `/login`, `/forgot-password`, `/auth/callback`, `robots.txt`, `sitemap.xml` requires a signed-in, approved user (`src/proxy.ts`); `/admin/*` requires the teacher role.
- Known limits: file *type* is checked in the browser only (one bucket also holds zips/notebooks); there are no email notifications (needs an email provider key).

## Checks
```bash
npm run types:check && npm test
```
(`npm run lint` is currently broken: typescript-eslint does not support TypeScript 7 yet.) CI runs the same on every push (`.github/workflows/ci.yml`).
