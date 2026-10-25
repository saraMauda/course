import Link from 'next/link';
import { redirect } from 'next/navigation';
import { createClient, supabaseConfigured } from '@/lib/supabase/server';
import { GradeForm } from '@/components/grade-form';

export default async function SubmissionsPage({ searchParams }: { searchParams: Promise<{ assignment?: string }> }) {
  if (!supabaseConfigured) redirect('/dashboard');
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect('/login');
  const { data: me } = await supabase.from('profiles').select('role').eq('id', user.id).single();
  if (me?.role !== 'teacher') redirect('/dashboard');

  const [{ data: assignments }, { data: all }, { data: students }] = await Promise.all([
    supabase.from('assignments').select('id, title, kind').order('id'),
    supabase.from('submissions').select('assignment_id, grade'),
    supabase.from('profiles').select('id, full_name').eq('role', 'student'),
  ]);

  const pendingBy = new Map<number, number>();
  const submittedBy = new Map<number, number>();
  for (const s of all ?? []) {
    submittedBy.set(s.assignment_id, (submittedBy.get(s.assignment_id) ?? 0) + 1);
    if (s.grade === null) pendingBy.set(s.assignment_id, (pendingBy.get(s.assignment_id) ?? 0) + 1);
  }

  const { assignment: param } = await searchParams;
  // default: the first assignment that has something waiting for review
  const firstPending = (assignments ?? []).find((a) => (pendingBy.get(a.id) ?? 0) > 0)?.id;
  const assignmentId = Number(param) || firstPending || assignments?.[0]?.id;
  const current = assignments?.find((a) => a.id === assignmentId);

  const { data: subs } = assignmentId
    ? await supabase
        .from('submissions')
        .select('id, student_id, repo_url, screenshot_path, file_path, notes, submitted_at, grade, feedback, graded_at')
        .eq('assignment_id', assignmentId)
        .order('submitted_at')
    : { data: [] };

  // private bucket: short-lived signed links, generated with the teacher's own session
  const paths = (subs ?? []).flatMap((s) => [s.screenshot_path, s.file_path]).filter((p): p is string => Boolean(p));
  const signed = new Map<string, string>();
  if (paths.length) {
    const { data } = await supabase.storage.from('submissions').createSignedUrls(paths, 3600);
    for (const d of data ?? []) if (d.path && d.signedUrl) signed.set(d.path, d.signedUrl);
  }
  const nameOf = (id: string) => students?.find((s) => s.id === id)?.full_name || 'ללא שם';

  return (
    <main className="p-6 max-w-4xl mx-auto space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-bold">בדיקת הגשות</h1>
        <Link href="/admin" className="rounded-lg border px-3 py-1.5 text-sm font-medium hover:bg-fd-accent">
          חזרה לניהול
        </Link>
      </div>

      <nav className="flex flex-wrap gap-1.5" aria-label="בחירת משימה">
        {(assignments ?? []).map((a) => {
          const pending = pendingBy.get(a.id) ?? 0;
          return (
            <Link
              key={a.id}
              href={`/admin/submissions?assignment=${a.id}`}
              className={`rounded-lg border px-3 py-1 text-sm ${
                a.id === assignmentId ? 'border-fd-primary bg-fd-primary text-fd-primary-foreground' : 'hover:bg-fd-accent'
              }`}
            >
              {a.kind === 'project' ? a.title : a.id}
              {pending > 0 && <span className="ms-1.5 rounded-full bg-amber-500 px-1.5 text-xs text-white">{pending}</span>}
            </Link>
          );
        })}
      </nav>

      <h2 className="text-lg font-semibold">
        {current?.title ?? 'אין משימות'} · {submittedBy.get(assignmentId ?? 0) ?? 0} הגשות
      </h2>

      <ul className="space-y-4">
        {(subs ?? []).map((s) => (
          <li key={s.id} className="space-y-3 rounded-xl border p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-semibold">{nameOf(s.student_id)}</span>
              <span className="text-sm text-fd-muted-foreground">
                {new Date(s.submitted_at).toLocaleString('he-IL')} ·{' '}
                {s.graded_at ? `נבדק, ציון ${s.grade}` : 'ממתין לבדיקה'}
              </span>
            </div>
            <div className="flex flex-wrap gap-2 text-sm">
              {s.repo_url && (
                <a href={s.repo_url} target="_blank" rel="noreferrer" className="rounded-lg border px-3 py-1 hover:bg-fd-accent">
                  קישור ל-Git
                </a>
              )}
              {s.file_path && signed.get(s.file_path) && (
                <a href={signed.get(s.file_path)} target="_blank" rel="noreferrer" className="rounded-lg border px-3 py-1 hover:bg-fd-accent">
                  הקובץ שהוגש
                </a>
              )}
            </div>
            {s.notes && <p className="text-sm text-fd-muted-foreground">הערת תלמידה: {s.notes}</p>}
            {s.screenshot_path && signed.get(s.screenshot_path) && (
              <a href={signed.get(s.screenshot_path)} target="_blank" rel="noreferrer" className="block">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={signed.get(s.screenshot_path)} alt="צילום מסך שהוגש" className="max-h-72 rounded-lg border" />
              </a>
            )}
            <GradeForm submissionId={s.id} grade={s.grade} feedback={s.feedback} graded={Boolean(s.graded_at)} />
          </li>
        ))}
        {!subs?.length && <li className="rounded-xl border p-4 text-fd-muted-foreground">עדיין אין הגשות למשימה הזו.</li>}
      </ul>
    </main>
  );
}
