import Link from 'next/link';
import { requireTeacher } from '@/lib/admin';
import { GradeForm } from '@/components/grade-form';
import { ItemChecks, type ItemView } from '@/components/item-checks';
import { projectItems } from '@/lib/project-items';
import { isNotebookPath } from '@/lib/notebook';

export const metadata = { title: 'בדיקת הגשות' };

type StoredItems = Record<string, { text?: string; path?: string }>;
const IMAGE_RE = /\.(png|jpe?g|gif|webp|svg)$/i;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default async function SubmissionsPage({
  searchParams,
}: {
  searchParams: Promise<{ assignment?: string; show?: string; student?: string }>;
}) {
  const { supabase } = await requireTeacher();

  const [{ data: assignments }, { data: all }, { data: students }] = await Promise.all([
    supabase.from('assignments').select('id, title, kind').order('id'),
    supabase.from('submissions').select('assignment_id, student_id, grade'),
    supabase.from('profiles').select('id, full_name, approved').eq('role', 'student').order('full_name'),
  ]);

  const pendingBy = new Map<number, number>();
  const submittedBy = new Map<number, number>();
  for (const s of all ?? []) {
    submittedBy.set(s.assignment_id, (submittedBy.get(s.assignment_id) ?? 0) + 1);
    if (s.grade === null) pendingBy.set(s.assignment_id, (pendingBy.get(s.assignment_id) ?? 0) + 1);
  }

  const { assignment: param, show, student: studentParam } = await searchParams;
  const onlyPending = show === 'pending';
  const studentFilter = studentParam && UUID.test(studentParam) ? studentParam : undefined;
  // default: the first assignment that has something waiting for review
  const firstPending = (assignments ?? []).find((a) => (pendingBy.get(a.id) ?? 0) > 0)?.id;
  const assignmentId = Number(param) || firstPending || assignments?.[0]?.id;
  const current = assignments?.find((a) => a.id === assignmentId);

  let query = assignmentId
    ? supabase
        .from('submissions')
        .select('id, student_id, repo_url, screenshot_path, file_path, items, notes, submitted_at, grade, feedback, graded_at')
        .eq('assignment_id', assignmentId)
        .order('submitted_at')
    : null;
  if (query && onlyPending) query = query.is('graded_at', null);
  if (query && studentFilter) query = query.eq('student_id', studentFilter);
  const { data: subs } = query ? await query : { data: [] };

  // private bucket: short-lived signed links, generated with the teacher's own session
  const paths = (subs ?? [])
    .flatMap((s) => [s.screenshot_path, s.file_path, ...Object.values((s.items ?? {}) as StoredItems).map((i) => i.path)])
    .filter((p): p is string => Boolean(p));
  const signed = new Map<string, string>();
  if (paths.length) {
    const { data } = await supabase.storage.from('submissions').createSignedUrls(paths, 3600);
    for (const d of data ?? []) if (d.path && d.signedUrl) signed.set(d.path, d.signedUrl);
  }
  const project = Object.values(projectItems).find((p) => p.assignmentId === assignmentId);
  const checksBy = new Map<number, Record<string, boolean>>();
  if (project && subs?.length) {
    const { data } = await supabase
      .from('submission_checks')
      .select('submission_id, item_key, ok')
      .in('submission_id', subs.map((s) => s.id));
    for (const c of data ?? []) checksBy.set(c.submission_id, { ...checksBy.get(c.submission_id), [c.item_key]: c.ok });
  }
  const nameOf = (id: string) => students?.find((s) => s.id === id)?.full_name || 'ללא שם';

  // approved students with nothing submitted for this assignment
  const submittedHere = new Set((all ?? []).filter((s) => s.assignment_id === assignmentId).map((s) => s.student_id));
  const missing = (students ?? []).filter((s) => s.approved && !submittedHere.has(s.id));

  const tab = (extra: string) => `/admin/submissions?assignment=${assignmentId}${extra}`;
  const chip = 'rounded-lg border px-3 py-1 text-sm';

  return (
    <main className="mx-auto max-w-4xl space-y-5 p-4 sm:p-6">
      <h1 className="text-2xl font-bold">בדיקת הגשות</h1>

      <nav className="flex flex-wrap gap-1.5" aria-label="בחירת משימה">
        {(assignments ?? []).map((a) => {
          const pending = pendingBy.get(a.id) ?? 0;
          return (
            <Link
              key={a.id}
              href={`/admin/submissions?assignment=${a.id}${onlyPending ? '&show=pending' : ''}`}
              title={a.title}
              className={`${chip} ${a.id === assignmentId ? 'border-fd-primary bg-fd-primary text-fd-primary-foreground' : 'hover:bg-fd-accent'}`}
            >
              {a.kind === 'project' ? a.title : a.id}
              {pending > 0 && <span className="ms-1.5 rounded-full bg-amber-500 px-1.5 text-xs text-white">{pending}</span>}
            </Link>
          );
        })}
      </nav>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">
          {current?.title ?? 'אין משימות'} · {submittedBy.get(assignmentId ?? 0) ?? 0} הגשות
        </h2>
        <div className="flex flex-wrap items-center gap-1.5">
          <Link href={tab('')} className={`${chip} ${!onlyPending ? 'bg-fd-accent' : 'hover:bg-fd-accent'}`}>
            הכול
          </Link>
          <Link href={tab('&show=pending')} className={`${chip} ${onlyPending ? 'bg-fd-accent' : 'hover:bg-fd-accent'}`}>
            רק ממתינות לבדיקה
          </Link>
          {studentFilter && (
            <Link href={tab(onlyPending ? '&show=pending' : '')} className={`${chip} border-fd-primary`}>
              {nameOf(studentFilter)} ✕
            </Link>
          )}
        </div>
      </div>

      <ul className="space-y-4">
        {(subs ?? []).map((s) => {
          const itemPaths = Object.values((s.items ?? {}) as StoredItems).map((i) => i.path);
          return (
            <li key={s.id} id={`s${s.id}`} className="space-y-3 rounded-xl border p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <Link href={`/admin/students/${s.student_id}`} className="font-semibold hover:underline">
                  {nameOf(s.student_id)}
                </Link>
                <span className="text-sm text-fd-muted-foreground">
                  {new Date(s.submitted_at).toLocaleString('he-IL')} · {s.graded_at ? `נבדק, ציון ${s.grade}` : 'ממתין לבדיקה'}
                </span>
              </div>
              <div className="flex flex-wrap gap-2 text-sm">
                {s.repo_url && (
                  <a href={s.repo_url} target="_blank" rel="noreferrer" className="rounded-lg border px-3 py-1 hover:bg-fd-accent">
                    קישור ל-Git
                  </a>
                )}
                {s.file_path && isNotebookPath(s.file_path) && (
                  <Link href={`/admin/notebook?path=${encodeURIComponent(s.file_path)}`} className="rounded-lg bg-fd-primary px-3 py-1 text-fd-primary-foreground">
                    צפייה ב-notebook
                  </Link>
                )}
                {s.file_path && signed.get(s.file_path) && (
                  <a href={signed.get(s.file_path)} target="_blank" rel="noreferrer" className="rounded-lg border px-3 py-1 hover:bg-fd-accent">
                    הקובץ שהוגש
                  </a>
                )}
                {!project && itemPaths.filter(isNotebookPath).map((p) => (
                  <Link key={p} href={`/admin/notebook?path=${encodeURIComponent(p)}`} className="rounded-lg bg-fd-primary px-3 py-1 text-fd-primary-foreground">
                    צפייה ב-notebook
                  </Link>
                ))}
              </div>
              {s.notes && <p className="text-sm text-fd-muted-foreground">הערת תלמידה: {s.notes}</p>}
              {s.screenshot_path && signed.get(s.screenshot_path) && (
                <a href={signed.get(s.screenshot_path)} target="_blank" rel="noreferrer" className="block">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={signed.get(s.screenshot_path)} alt="צילום מסך שהוגש" className="max-h-72 rounded-lg border" />
                </a>
              )}
              {project && (
                <ItemChecks
                  submissionId={s.id}
                  initial={checksBy.get(s.id) ?? {}}
                  views={project.items.map((item): ItemView => {
                    const v = ((s.items ?? {}) as StoredItems)[item.key];
                    return {
                      item,
                      text: v?.text,
                      url: v?.path ? signed.get(v.path) : undefined,
                      isImage: v?.path ? IMAGE_RE.test(v.path) : false,
                      notebookPath: isNotebookPath(v?.path) ? v.path : undefined,
                    };
                  })}
                />
              )}
              <GradeForm submissionId={s.id} grade={s.grade} feedback={s.feedback} graded={Boolean(s.graded_at)} />
            </li>
          );
        })}
        {!subs?.length && (
          <li className="rounded-xl border p-4 text-fd-muted-foreground">
            {onlyPending || studentFilter ? 'אין הגשות שמתאימות לסינון.' : 'עדיין אין הגשות למשימה הזו.'}
          </li>
        )}
      </ul>

      {assignmentId && missing.length > 0 && (
        <section aria-labelledby="missing-h" className="space-y-2 rounded-xl border p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 id="missing-h" className="font-semibold">
              עוד לא הגישו ({missing.length})
            </h2>
            <Link
              href={`/admin/email?to=${missing.map((m) => m.id).join(',')}&template=builtin:missing`}
              className="rounded-lg bg-fd-primary px-3 py-1.5 text-sm font-medium text-fd-primary-foreground"
            >
              שליחת תזכורת לכולן
            </Link>
          </div>
          <p className="text-sm text-fd-muted-foreground">
            {missing.map((m, i) => (
              <span key={m.id}>
                {i > 0 && ', '}
                <Link href={`/admin/students/${m.id}`} className="hover:underline">
                  {m.full_name || 'ללא שם'}
                </Link>
              </span>
            ))}
          </p>
        </section>
      )}
    </main>
  );
}
