import Link from 'next/link';
import { redirect } from 'next/navigation';
import { createClient, supabaseConfigured } from '@/lib/supabase/server';
import { LessonDates } from '@/components/lesson-dates';
import { HOMEWORK_REMINDER_DAYS } from '@/lib/reminders';

export default async function LessonsPage() {
  if (!supabaseConfigured) redirect('/dashboard');
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect('/login');
  const { data: me } = await supabase.from('profiles').select('role').eq('id', user.id).single();
  if (me?.role !== 'teacher') redirect('/dashboard');

  const { data: lessons } = await supabase.from('lessons').select('id, title, held_on').order('id');

  return (
    <main className="p-6 max-w-3xl mx-auto space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-bold">תאריכי שיעורים ותזכורות</h1>
        <Link href="/admin" className="rounded-lg border px-3 py-1.5 text-sm font-medium hover:bg-fd-accent">
          חזרה לניהול
        </Link>
      </div>
      <div className="rounded-xl border bg-fd-muted/40 p-4 text-sm text-fd-muted-foreground">
        <p className="mb-1 font-medium text-fd-foreground">מה נשלח אוטומטית (בדיקה יומית, בערך 08:00–09:00):</p>
        <ul className="list-disc space-y-1 ps-5">
          <li>{HOMEWORK_REMINDER_DAYS} ימים לפני שיעור: מייל לכל תלמידה מאושרת שלא הגישה את שיעורי הבית של השיעור הקודם.</li>
          <li>יום לפני שיעור: תזכורת שיעור לכל התלמידות המאושרות.</li>
          <li>כל תזכורת נשלחת פעם אחת בלבד לכל תלמידה. שיעור בלי תאריך לא מקבל תזכורות.</li>
        </ul>
      </div>
      <LessonDates lessons={lessons ?? []} />
    </main>
  );
}
