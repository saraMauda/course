import { requireTeacher } from '@/lib/admin';
import { LessonDates } from '@/components/lesson-dates';
import { LessonVideos } from '@/components/lesson-videos';
import { HOMEWORK_REMINDER_DAYS } from '@/lib/reminders';

export const metadata = { title: 'שיעורים ותאריכים' };

export default async function LessonsPage() {
  const { supabase } = await requireTeacher();
  const { data: lessons } = await supabase.from('lessons').select('id, title, held_on').order('id');
  // separate query: the dates keep working even before 009-lesson-video.sql was run
  const { data: videos } = await supabase.from('lessons').select('id, title, video_url').order('id');

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
      <a href="#videos" className="inline-block text-sm font-medium text-fd-primary hover:underline">
        מעבר לסרטוני השיעורים
      </a>
      <LessonDates lessons={lessons ?? []} />
      <section id="videos" className="scroll-mt-20 space-y-3 pt-4">
        <h2 className="text-xl font-bold">סרטוני השיעורים</h2>
        <p className="text-sm text-fd-muted-foreground">
          מדביקים קישור שיתוף מ-Google Drive, והסרטון מופיע בדף השיעור. חשוב ששיתוף הקובץ ב-Drive יאפשר לתלמידות לצפות. כדי להסיר
          סרטון מוחקים את הקישור ושומרים.
        </p>
        {videos ? (
          <LessonVideos lessons={videos} />
        ) : (
          <p role="alert" className="rounded-xl border p-4 text-sm text-red-600">
            כדי להוסיף סרטונים צריך להריץ פעם אחת את הקובץ supabase/009-lesson-video.sql ב-SQL Editor של Supabase.
          </p>
        )}
      </section>
    </main>
  );
}
