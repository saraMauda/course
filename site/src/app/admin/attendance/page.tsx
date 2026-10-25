import Link from 'next/link';
import { redirect } from 'next/navigation';
import { createClient, supabaseConfigured } from '@/lib/supabase/server';
import { AttendanceSheet } from '@/components/attendance-sheet';

export default async function AttendancePage({ searchParams }: { searchParams: Promise<{ lesson?: string }> }) {
  if (!supabaseConfigured) redirect('/dashboard');
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect('/login');
  const { data: me } = await supabase.from('profiles').select('role').eq('id', user.id).single();
  if (me?.role !== 'teacher') redirect('/dashboard');

  const [{ data: lessons }, { data: students }] = await Promise.all([
    supabase.from('lessons').select('id, title').order('id'),
    supabase.from('profiles').select('id, full_name').eq('role', 'student').eq('approved', true).order('full_name'),
  ]);

  const { lesson: lessonParam } = await searchParams;
  const lessonId = Number(lessonParam) || lessons?.[0]?.id || 1;
  const current = lessons?.find((l) => l.id === lessonId);

  const { data: rows } = await supabase.from('attendance').select('student_id, status').eq('lesson_id', lessonId);
  const initial = Object.fromEntries((rows ?? []).map((r) => [r.student_id, r.status]));

  return (
    <main className="p-6 max-w-3xl mx-auto space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-bold">נוכחות</h1>
        <Link href="/admin" className="rounded-lg border px-3 py-1.5 text-sm font-medium hover:bg-fd-accent">
          חזרה לניהול
        </Link>
      </div>

      {!lessons?.length ? (
        <p className="rounded-xl border p-4 text-fd-muted-foreground">
          אין שיעורים בטבלה. צריך להריץ ב-Supabase את הקובץ <code>supabase/seed.sql</code>.
        </p>
      ) : (
        <>
          <nav className="flex flex-wrap gap-1.5" aria-label="בחירת שיעור">
            {lessons.map((l) => (
              <Link
                key={l.id}
                href={`/admin/attendance?lesson=${l.id}`}
                className={`rounded-lg border px-3 py-1 text-sm ${
                  l.id === lessonId ? 'bg-fd-primary text-fd-primary-foreground border-fd-primary' : 'hover:bg-fd-accent'
                }`}
              >
                {l.id}
              </Link>
            ))}
          </nav>
          <h2 className="text-lg font-semibold">
            שיעור {lessonId}
            {current ? ` · ${current.title}` : ''}
          </h2>
          <AttendanceSheet key={lessonId} lessonId={lessonId} students={students ?? []} initial={initial} />
        </>
      )}
    </main>
  );
}
