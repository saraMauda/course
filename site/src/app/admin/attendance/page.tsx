import Link from 'next/link';
import { requireTeacher } from '@/lib/admin';
import { AttendanceSheet } from '@/components/attendance-sheet';
import { todayInIsrael } from '@/lib/reminders';

export default async function AttendancePage({ searchParams }: { searchParams: Promise<{ lesson?: string }> }) {
  const { supabase } = await requireTeacher();

  const [{ data: lessons }, { data: students }] = await Promise.all([
    supabase.from('lessons').select('id, title, held_on').order('id'),
    supabase.from('profiles').select('id, full_name').eq('role', 'student').eq('approved', true).order('full_name'),
  ]);

  const { lesson: lessonParam } = await searchParams;
  // default to the latest lesson that has already been held, otherwise the first
  const today = todayInIsrael();
  const latestHeld = [...(lessons ?? [])].reverse().find((l) => l.held_on && l.held_on <= today)?.id;
  const lessonId = Number(lessonParam) || latestHeld || lessons?.[0]?.id || 1;
  const current = lessons?.find((l) => l.id === lessonId);

  const { data: rows } = await supabase.from('attendance').select('student_id, status').eq('lesson_id', lessonId);
  const initial = Object.fromEntries((rows ?? []).map((r) => [r.student_id, r.status]));

  return (
    <main className="p-6 max-w-3xl mx-auto space-y-5">
      <h1 className="text-2xl font-bold">נוכחות</h1>

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
                title={l.held_on ? new Date(`${l.held_on}T12:00:00Z`).toLocaleDateString('he-IL') : undefined}
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
            {current?.held_on && (
              <span className="ms-2 text-sm font-normal text-fd-muted-foreground">
                {new Date(`${current.held_on}T12:00:00Z`).toLocaleDateString('he-IL', { weekday: 'long', day: 'numeric', month: 'long' })}
              </span>
            )}
          </h2>
          <AttendanceSheet key={lessonId} lessonId={lessonId} students={students ?? []} initial={initial} />
        </>
      )}
    </main>
  );
}
