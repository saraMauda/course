import Link from 'next/link';
import { SignOutButton } from '@/components/sign-out-button';
import { redirect } from 'next/navigation';
import { createClient, supabaseConfigured } from '@/lib/supabase/server';
import { finalGrade, attendancePercent, defaultWeights, type Weights } from '@/lib/grades';
import course from '@/lib/course.json';
import { projectItems } from '@/lib/project-items';

export const metadata = { title: 'האזור האישי', robots: { index: false, follow: false } };

const dateFmt = new Intl.DateTimeFormat('he-IL', { dateStyle: 'medium', timeZone: 'Asia/Jerusalem' });
const projectHref = (id: number) => {
  const n = Object.entries(projectItems).find(([, p]) => p.assignmentId === id)?.[0];
  return n ? `/docs/projects/project-0${n}` : null;
};

export default async function DashboardPage() {
  if (!supabaseConfigured) return <SetupNotice />;
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect('/login');

  const [{ data: profile }, { data: assignments }, { data: subs }, { data: attendance }, { data: w }, { data: exam }, { data: done }] =
    await Promise.all([
      supabase.from('profiles').select('full_name, role').eq('id', user.id).single(),
      supabase.from('assignments').select('id, kind, title, due_at, lesson_id').order('id'),
      supabase.from('submissions').select('assignment_id, grade, feedback, submitted_at, graded_at').eq('student_id', user.id),
      supabase.from('attendance').select('status').eq('student_id', user.id),
      supabase.from('grade_weights').select('category, weight'),
      supabase.from('exam_grades').select('grade').eq('student_id', user.id).maybeSingle(),
      supabase.from('lesson_progress').select('lesson_id').eq('student_id', user.id),
    ]);

  if (profile?.role === 'teacher') redirect('/admin');

  const weights = {
    ...defaultWeights,
    ...Object.fromEntries((w ?? []).map((r) => [r.category, Number(r.weight)])),
  } as Weights;
  const final = finalGrade(assignments ?? [], subs ?? [], weights, exam ? Number(exam.grade) : null);
  const att = attendancePercent(attendance ?? []);
  const now = new Date();
  const TOTAL_LESSONS = course.lessons.length;
  const doneIds = new Set((done ?? []).map((d) => d.lesson_id));
  const doneCount = course.lessons.filter((l) => doneIds.has(Number(l.num))).length;
  const nextLesson = course.lessons.find((l) => !doneIds.has(Number(l.num)));

  return (
    <main className="p-6 max-w-3xl mx-auto space-y-8">
      <header>
        <div className="flex items-center justify-between gap-2">
          <h1 className="text-2xl font-bold">שלום {profile?.full_name || ''}</h1>
          <SignOutButton />
        </div>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Stat label="ציון מבחן" value={exam ? String(exam.grade) : '—'} />
          <Stat label="ציון משוער" value={final === null ? '—' : final.toFixed(1)} />
          <Stat label="נוכחות" value={att === null ? '—' : `${att.toFixed(0)}%`} />
        </div>
      </header>
      <section aria-labelledby="progress-h">
        <h2 id="progress-h" className="text-xl font-semibold mb-3">
          התקדמות בקורס
        </h2>
        <div className="flex items-center gap-3">
          <div
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={TOTAL_LESSONS}
            aria-valuenow={doneCount}
            aria-label="שיעורים שהושלמו"
            className="h-3 flex-1 overflow-hidden rounded-full bg-fd-muted"
          >
            <div className="h-full bg-fd-primary" style={{ width: `${(100 * doneCount) / TOTAL_LESSONS}%` }} />
          </div>
          <span className="text-sm text-fd-muted-foreground">
            {doneCount}/{TOTAL_LESSONS} שיעורים
          </span>
        </div>
        {nextLesson && (
          <p className="mt-2 text-sm">
            השיעור הבא:{' '}
            <Link href={nextLesson.slug} className="underline">
              שיעור {nextLesson.num} – {nextLesson.title}
            </Link>
          </p>
        )}
      </section>
      <section aria-labelledby="subs-h">
        <h2 id="subs-h" className="text-xl font-semibold mb-3">
          הגשות
        </h2>
        <ul className="divide-y rounded-xl border">
          {(assignments ?? []).map((a) => {
            const s = subs?.find((x) => x.assignment_id === a.id);
            const href =
              a.kind === 'project'
                ? projectHref(a.id)
                : a.lesson_id
                  ? `/docs/lessons/lesson-${String(a.lesson_id).padStart(2, '0')}/homework`
                  : null;
            const due = a.due_at ? new Date(a.due_at) : null;
            const late = due && (s ? new Date(s.submitted_at) > due : now > due);
            return (
              <li key={a.id} className="space-y-1 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  {href ? (
                    <Link href={href} className="font-medium hover:underline">
                      {a.title}
                    </Link>
                  ) : (
                    <span className="font-medium">{a.title}</span>
                  )}
                  <span className="text-sm text-fd-muted-foreground">
                    {s ? (s.grade === null ? 'הוגש – ממתין לבדיקה' : `ציון ${s.grade}`) : 'לא הוגש'}
                  </span>
                </div>
                <div className="flex flex-wrap gap-x-4 text-xs text-fd-muted-foreground">
                  {due && <span>להגשה עד {dateFmt.format(due)}</span>}
                  {s && <span>הוגש ב-{dateFmt.format(new Date(s.submitted_at))}</span>}
                  {late && <span className="font-medium text-red-600 dark:text-red-400">{s ? 'הוגש באיחור' : 'עבר מועד ההגשה'}</span>}
                </div>
                {s?.feedback && (
                  <p className="whitespace-pre-wrap rounded-lg bg-fd-muted p-2 text-sm">
                    <span className="font-medium">משוב מהמרצה: </span>
                    {s.feedback}
                  </p>
                )}
              </li>
            );
          })}
          {!assignments?.length && <li className="p-3 text-fd-muted-foreground">אין עדיין משימות.</li>}
        </ul>
      </section>
      <Link href="/docs" className="underline">
        לחומרי הקורס
      </Link>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border p-4">
      <div className="text-sm text-fd-muted-foreground">{label}</div>
      <div className="text-3xl font-bold">{value}</div>
    </div>
  );
}

function SetupNotice() {
  return (
    <main className="p-8 max-w-xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">האזור האישי עדיין לא מחובר</h1>
      <p className="text-fd-muted-foreground">
        יש ליצור פרויקט ב-Supabase, להריץ את <code>supabase/schema.sql</code>, ולהעתיק את <code>.env.example</code> ל-
        <code>.env.local</code> עם המפתחות.
      </p>
    </main>
  );
}
