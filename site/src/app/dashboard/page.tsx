import Link from 'next/link';
import { redirect } from 'next/navigation';
import { createClient, supabaseConfigured } from '@/lib/supabase/server';
import { finalGrade, attendancePercent, defaultWeights, type Weights } from '@/lib/grades';

export default async function DashboardPage() {
  if (!supabaseConfigured) return <SetupNotice />;
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect('/login');

  const [{ data: profile }, { data: assignments }, { data: subs }, { data: attendance }, { data: w }, { data: exam }] =
    await Promise.all([
      supabase.from('profiles').select('full_name, role').eq('id', user.id).single(),
      supabase.from('assignments').select('id, kind, title, due_at').order('id'),
      supabase.from('submissions').select('assignment_id, grade, feedback, submitted_at').eq('student_id', user.id),
      supabase.from('attendance').select('status').eq('student_id', user.id),
      supabase.from('grade_weights').select('category, weight'),
      supabase.from('exam_grades').select('grade').eq('student_id', user.id).maybeSingle(),
    ]);

  if (profile?.role === 'teacher') redirect('/admin');

  const weights = {
    ...defaultWeights,
    ...Object.fromEntries((w ?? []).map((r) => [r.category, Number(r.weight)])),
  } as Weights;
  const final = finalGrade(assignments ?? [], subs ?? [], weights, exam ? Number(exam.grade) : null);
  const att = attendancePercent(attendance ?? []);

  return (
    <main className="p-6 max-w-3xl mx-auto space-y-8">
      <header>
        <h1 className="text-2xl font-bold">שלום {profile?.full_name || ''}</h1>
        <div className="mt-4 grid grid-cols-3 gap-4">
          <Stat label="ציון מבחן" value={exam ? String(exam.grade) : '—'} />
          <Stat label="ציון משוער" value={final === null ? '—' : final.toFixed(1)} />
          <Stat label="נוכחות" value={att === null ? '—' : `${att.toFixed(0)}%`} />
        </div>
      </header>
      <section>
        <h2 className="text-xl font-semibold mb-3">הגשות</h2>
        <ul className="divide-y rounded-xl border">
          {(assignments ?? []).map((a) => {
            const s = subs?.find((x) => x.assignment_id === a.id);
            return (
              <li key={a.id} className="flex items-center justify-between p-3">
                <span>{a.title}</span>
                <span className="text-sm text-fd-muted-foreground">
                  {s ? (s.grade === null ? 'הוגש – ממתין לבדיקה' : `ציון ${s.grade}`) : 'לא הוגש'}
                </span>
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
