import { requireTeacher } from '@/lib/admin';
import { LessonDates } from '@/components/lesson-dates';
import { HOMEWORK_REMINDER_DAYS } from '@/lib/reminders';

export const metadata = { title: 'שיעורים ותאריכים' };

export default async function LessonsPage() {
  const { supabase } = await requireTeacher();
  const { data: lessons } = await supabase.from('lessons').select('id, title, held_on').order('id');

  return (
    <main className="mx-auto max-w-3xl space-y-5 p-4 sm:p-6">
      <h1 className="text-2xl font-bold">שיעורים ותאריכים</h1>
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
