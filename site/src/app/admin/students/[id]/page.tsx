import Link from 'next/link';
import { notFound } from 'next/navigation';
import { requireTeacher } from '@/lib/admin';
import { ApproveButton } from '@/components/approve-button';
import { ExamGradeInput } from '@/components/exam-grade-input';
import { finalGrade, attendancePercent, defaultWeights, type Weights } from '@/lib/grades';

export const metadata = { title: 'כרטיס תלמידה' };

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const ATT: Record<string, string> = { present: 'נוכחת', late: 'איחור', absent: 'חסרה', excused: 'מוצדק' };
const dateFmt = new Intl.DateTimeFormat('he-IL', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Jerusalem' });
const dayFmt = new Intl.DateTimeFormat('he-IL', { dateStyle: 'medium', timeZone: 'Asia/Jerusalem' });

export default async function StudentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!UUID.test(id)) notFound();
  const { supabase } = await requireTeacher();

  const [{ data: student }, { data: email }, { data: assignments }, { data: subs }, { data: attendance }, { data: lessons }, { data: done }, { data: exam }, { data: w }, { data: sent }] =
    await Promise.all([
      supabase.from('profiles').select('id, full_name, approved, created_at').eq('id', id).eq('role', 'student').maybeSingle(),
      supabase.rpc('student_email', { student: id }),
      supabase.from('assignments').select('id, title, kind, due_at, lesson_id').order('id'),
      supabase.from('submissions').select('assignment_id, grade, submitted_at, graded_at').eq('student_id', id),
      supabase.from('attendance').select('lesson_id, status').eq('student_id', id),
      supabase.from('lessons').select('id, title, held_on').order('id'),
      supabase.from('lesson_progress').select('lesson_id').eq('student_id', id),
      supabase.from('exam_grades').select('grade').eq('student_id', id).maybeSingle(),
      supabase.from('grade_weights').select('category, weight'),
      supabase.from('email_log').select('id, subject, status, sent_at').eq('student_id', id).order('sent_at', { ascending: false }).limit(8),
    ]);
  if (!student) notFound();

  const weights = { ...defaultWeights, ...Object.fromEntries((w ?? []).map((r) => [r.category, Number(r.weight)])) } as Weights;
  const examGrade = exam ? Number(exam.grade) : null;
  const final = finalGrade(assignments ?? [], subs ?? [], weights, examGrade);
  const att = attendancePercent(attendance ?? []);
  const now = new Date();

  return (
    <main className="mx-auto max-w-4xl space-y-6 p-4 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link href="/admin" className="text-sm text-fd-muted-foreground hover:underline">
            ← כל התלמידות
          </Link>
          <h1 className="text-2xl font-bold">{student.full_name || 'ללא שם'}</h1>
          <p dir="ltr" className="text-start text-sm text-fd-muted-foreground">
            {email || 'אין כתובת מייל'}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ApproveButton studentId={student.id} approved={student.approved} />
          {email && (
            <Link href={`/admin/email?to=${student.id}`} className="rounded-lg bg-fd-primary px-3 py-1.5 text-sm font-medium text-fd-primary-foreground">
              שליחת מייל
            </Link>
          )}
        </div>
      </div>

      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4" aria-label="סיכום">
        <Card label="ציון משוער" value={final === null ? '—' : final.toFixed(1)} />
        <Card label="נוכחות" value={att === null ? '—' : `${att.toFixed(0)}%`} />
        <Card label="שיעורים שסומנו כהושלמו" value={`${done?.length ?? 0}/${lessons?.length ?? 0}`} />
        <div className="rounded-xl border p-4">
          <div className="text-sm text-fd-muted-foreground">ציון מבחן</div>
          <div className="mt-1">
            <ExamGradeInput studentId={student.id} initial={examGrade} />
          </div>
        </div>
      </section>

      <section aria-labelledby="subs-h" className="space-y-2">
        <h2 id="subs-h" className="text-lg font-semibold">
          הגשות
        </h2>
        <ul className="divide-y rounded-xl border">
          {(assignments ?? []).map((a) => {
            const s = subs?.find((x) => x.assignment_id === a.id);
            const due = a.due_at ? new Date(a.due_at) : null;
            const late = due && (s ? new Date(s.submitted_at) > due : now > due);
            return (
              <li key={a.id} className="flex flex-wrap items-center justify-between gap-2 p-3">
                <span className="font-medium">{a.title}</span>
                <span className="flex flex-wrap items-center gap-3 text-sm">
                  {late && <span className="text-red-600">{s ? 'באיחור' : 'עבר המועד'}</span>}
                  <span className="text-fd-muted-foreground">
                    {!s ? 'לא הוגש' : s.graded_at ? `ציון ${s.grade}` : 'ממתין לבדיקה'}
                    {s && ` · ${dayFmt.format(new Date(s.submitted_at))}`}
                  </span>
                  {s && (
                    <Link href={`/admin/submissions?assignment=${a.id}&student=${student.id}`} className="text-fd-primary underline">
                      לבדיקה
                    </Link>
                  )}
                </span>
              </li>
            );
          })}
        </ul>
      </section>

      <section aria-labelledby="att-h" className="space-y-2">
        <h2 id="att-h" className="text-lg font-semibold">
          נוכחות לפי שיעור
        </h2>
        <ul className="grid gap-2 sm:grid-cols-2">
          {(lessons ?? []).map((l) => {
            const status = attendance?.find((x) => x.lesson_id === l.id)?.status;
            return (
              <li key={l.id} className="flex items-center justify-between gap-2 rounded-lg border p-2.5 text-sm">
                <span>
                  שיעור {l.id}
                  {l.held_on && <span className="text-fd-muted-foreground"> · {dayFmt.format(new Date(`${l.held_on}T12:00:00Z`))}</span>}
                </span>
                <span className={status === 'absent' ? 'text-red-600' : status ? '' : 'text-fd-muted-foreground'}>{status ? ATT[status] : 'לא סומן'}</span>
              </li>
            );
          })}
        </ul>
      </section>

      <section aria-labelledby="mail-h" className="space-y-2">
        <h2 id="mail-h" className="text-lg font-semibold">
          מיילים אחרונים אליה
        </h2>
        {sent?.length ? (
          <ul className="divide-y rounded-xl border text-sm">
            {sent.map((m) => (
              <li key={m.id} className="flex flex-wrap justify-between gap-2 p-3">
                <span>{m.subject}</span>
                <span className={m.status === 'failed' ? 'text-red-600' : 'text-fd-muted-foreground'}>
                  {m.status === 'failed' ? 'נכשל · ' : ''}
                  {dateFmt.format(new Date(m.sent_at))}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-fd-muted-foreground">עוד לא נשלחו אליה מיילים מהאתר.</p>
        )}
      </section>
    </main>
  );
}

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border p-4">
      <div className="text-sm text-fd-muted-foreground">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}
