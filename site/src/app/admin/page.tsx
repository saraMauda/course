import Link from 'next/link';
import { requireTeacher } from '@/lib/admin';
import { ApproveButton } from '@/components/approve-button';
import { StudentsTable, type StudentRow } from '@/components/students-table';
import { finalGrade, attendancePercent, defaultWeights, type Weights } from '@/lib/grades';
import { hebrewDate } from '@/lib/dates';
import { nextLesson } from '@/lib/email-templates';
import { daysBetween, todayInIsrael } from '@/lib/reminders';

export const metadata = { title: 'ניהול הקורס' };

export default async function AdminPage() {
  const { supabase } = await requireTeacher();

  const [{ data: students }, { data: assignments }, { data: subs }, { data: attendance }, { data: w }, { data: exams }, { data: lessons }] =
    await Promise.all([
      supabase.from('profiles').select('id, full_name, approved').eq('role', 'student').order('full_name'),
      supabase.from('assignments').select('id, kind'),
      supabase.from('submissions').select('student_id, assignment_id, grade'),
      supabase.from('attendance').select('student_id, status'),
      supabase.from('grade_weights').select('category, weight'),
      supabase.from('exam_grades').select('student_id, grade'),
      supabase.from('lessons').select('id, title, held_on'),
    ]);
  const weights = {
    ...defaultWeights,
    ...Object.fromEntries((w ?? []).map((r) => [r.category, Number(r.weight)])),
  } as Weights;

  const rows: StudentRow[] = (students ?? []).map((s) => {
    const mySubs = (subs ?? []).filter((x) => x.student_id === s.id);
    const myAtt = (attendance ?? []).filter((x) => x.student_id === s.id);
    const exam = (exams ?? []).find((x) => x.student_id === s.id)?.grade;
    return {
      id: s.id,
      full_name: s.full_name,
      approved: s.approved,
      exam: exam === undefined ? null : Number(exam),
      submitted: mySubs.length,
      pending: mySubs.filter((x) => x.grade === null).length,
      att: attendancePercent(myAtt),
      final: finalGrade(assignments ?? [], mySubs, weights, exam === undefined ? null : Number(exam)),
    };
  });

  const awaiting = rows.filter((r) => !r.approved);
  const active = rows.length - awaiting.length;
  const totalPending = rows.reduce((n, r) => n + r.pending, 0);
  const today = todayInIsrael();
  const next = nextLesson(lessons ?? [], today);
  const inDays = next?.held_on ? daysBetween(today, next.held_on) : null;

  return (
    <main className="mx-auto max-w-5xl space-y-6 p-4 sm:p-6">
      <h1 className="text-2xl font-bold">ניהול הקורס</h1>

      <section aria-label="סקירה" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="תלמידות פעילות" value={String(active)} />
        <Stat label="ממתינות לאישור" value={String(awaiting.length)} tone={awaiting.length ? 'warn' : undefined} />
        <Stat
          label="הגשות לבדיקה"
          value={String(totalPending)}
          tone={totalPending ? 'warn' : undefined}
          href={totalPending ? '/admin/submissions?show=pending' : undefined}
        />
        <Stat
          label="השיעור הבא"
          value={next ? `שיעור ${next.id}` : 'לא נקבע'}
          sub={
            next?.held_on
              ? `${hebrewDate(next.held_on)}${inDays === 0 ? ' · היום' : inDays === 1 ? ' · מחר' : ` · בעוד ${inDays} ימים`}`
              : 'אפשר להזין תאריכים בלשונית "שיעורים ותאריכים"'
          }
          href="/admin/lessons"
        />
      </section>

      {awaiting.length > 0 && (
        <section role="status" className="rounded-xl border border-amber-500/50 bg-amber-500/5 p-4">
          <h2 className="mb-3 font-semibold">ממתינות לאישור הרשמה ({awaiting.length})</h2>
          <ul className="space-y-2">
            {awaiting.map((r) => (
              <li key={r.id} className="flex items-center justify-between gap-3">
                <Link href={`/admin/students/${r.id}`} className="hover:underline">
                  {r.full_name || 'ללא שם'}
                </Link>
                <ApproveButton studentId={r.id} approved={false} />
              </li>
            ))}
          </ul>
        </section>
      )}

      <StudentsTable rows={rows} totalAssignments={assignments?.length ?? 0} />
    </main>
  );
}

function Stat({ label, value, sub, tone, href }: { label: string; value: string; sub?: string; tone?: 'warn'; href?: string }) {
  const body = (
    <div className={`h-full rounded-xl border p-4 ${tone === 'warn' ? 'border-amber-500/50 bg-amber-500/5' : ''} ${href ? 'hover:bg-fd-accent' : ''}`}>
      <div className="text-sm text-fd-muted-foreground">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
      {sub && <div className="mt-0.5 text-xs text-fd-muted-foreground">{sub}</div>}
    </div>
  );
  return href ? <Link href={href}>{body}</Link> : body;
}
