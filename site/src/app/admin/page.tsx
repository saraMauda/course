import Link from 'next/link';
import { redirect } from 'next/navigation';
import { createClient, supabaseConfigured } from '@/lib/supabase/server';
import { ExamGradeInput } from '@/components/exam-grade-input';
import { finalGrade, attendancePercent, defaultWeights, type Weights } from '@/lib/grades';

export default async function AdminPage() {
  if (!supabaseConfigured) redirect('/dashboard');
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect('/login');
  const { data: me } = await supabase.from('profiles').select('role').eq('id', user.id).single();
  if (me?.role !== 'teacher') redirect('/dashboard');

  const [{ data: students }, { data: assignments }, { data: subs }, { data: attendance }, { data: w }, { data: exams }] =
    await Promise.all([
      supabase.from('profiles').select('id, full_name').eq('role', 'student').order('full_name'),
      supabase.from('assignments').select('id, kind'),
      supabase.from('submissions').select('student_id, assignment_id, grade'),
      supabase.from('attendance').select('student_id, status'),
      supabase.from('grade_weights').select('category, weight'),
      supabase.from('exam_grades').select('student_id, grade'),
    ]);
  const weights = {
    ...defaultWeights,
    ...Object.fromEntries((w ?? []).map((r) => [r.category, Number(r.weight)])),
  } as Weights;

  const rows = (students ?? []).map((s) => {
    const mySubs = (subs ?? []).filter((x) => x.student_id === s.id);
    const myAtt = (attendance ?? []).filter((x) => x.student_id === s.id);
    const exam = (exams ?? []).find((x) => x.student_id === s.id)?.grade;
    return {
      ...s,
      exam: exam === undefined ? null : Number(exam),
      submitted: mySubs.length,
      pending: mySubs.filter((x) => x.grade === null).length,
      att: attendancePercent(myAtt),
      final: finalGrade(assignments ?? [], mySubs, weights, exam === undefined ? null : Number(exam)),
    };
  });

  return (
    <main className="p-6 max-w-4xl mx-auto">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-bold">ניהול הקורס</h1>
        <Link href="/docs" className="rounded-lg border px-3 py-1.5 text-sm font-medium hover:bg-fd-accent">
          לחומרי הקורס
        </Link>
      </div>
      <div className="overflow-x-auto rounded-xl border">
        <table className="w-full text-start">
          <thead className="bg-fd-muted">
            <tr>
              {['תלמידה', 'הגשות', 'ממתינות לבדיקה', 'נוכחות', 'ציון מבחן', 'ציון משוער'].map((h) => (
                <th key={h} className="p-3 text-start font-medium">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y">
            {rows.map((r) => (
              <tr key={r.id}>
                <td className="p-3">{r.full_name || '—'}</td>
                <td className="p-3">
                  {r.submitted}/{assignments?.length ?? 0}
                </td>
                <td className="p-3">{r.pending}</td>
                <td className="p-3">{r.att === null ? '—' : `${r.att.toFixed(0)}%`}</td>
                <td className="p-3">
                  <ExamGradeInput studentId={r.id} initial={r.exam} />
                </td>
                <td className="p-3 font-semibold">{r.final === null ? '—' : r.final.toFixed(1)}</td>
              </tr>
            ))}
            {!rows.length && (
              <tr>
                <td colSpan={6} className="p-3 text-fd-muted-foreground">
                  אין עדיין תלמידות רשומות.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}
