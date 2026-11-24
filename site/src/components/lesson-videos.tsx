'use client';

import { useState } from 'react';
import { createClient } from '@/lib/supabase/client';
import { parseDriveLink } from '@/lib/drive';

interface Lesson {
  id: number;
  title: string;
  video_url: string | null;
}

/** Teacher only: a Google Drive link for the recording of each lesson. */
export function LessonVideos({ lessons }: { lessons: Lesson[] }) {
  return (
    <ul className="divide-y rounded-xl border">
      {lessons.map((l) => (
        <VideoRow key={l.id} lesson={l} />
      ))}
    </ul>
  );
}

function VideoRow({ lesson }: { lesson: Lesson }) {
  const [saved, setSaved] = useState(lesson.video_url ?? '');
  const [value, setValue] = useState(saved);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    const link = parseDriveLink(value);
    if (value.trim() && !link) {
      return setMsg({ ok: false, text: 'זה לא קישור לקובץ ב-Drive. ב-Drive: שיתוף, העתקת הקישור, ולהדביק כאן.' });
    }
    if (!link && saved && !window.confirm(`להסיר את הסרטון משיעור ${lesson.id}?`)) return;
    setBusy(true);
    setMsg(null);
    const { data, error } = await createClient()
      .from('lessons')
      .update({ video_url: link?.url ?? null })
      .eq('id', lesson.id)
      .select('id');
    setBusy(false);
    // a blocked update is not an error: it just changes no rows
    if (error || !data?.length) return setMsg({ ok: false, text: 'השמירה נכשלה' });
    setSaved(link?.url ?? '');
    setValue(link?.url ?? '');
    setMsg({ ok: true, text: link ? 'הסרטון נשמר' : 'הסרטון הוסר' });
  }

  return (
    <li className="p-3">
      <form onSubmit={save} className="space-y-2">
        <label htmlFor={`video-${lesson.id}`} className="block">
          <span className="font-medium">שיעור {lesson.id}</span> · {lesson.title}
        </label>
        <div className="flex flex-wrap items-center gap-2">
          <input
            id={`video-${lesson.id}`}
            dir="ltr"
            inputMode="url"
            placeholder="https://drive.google.com/file/d/..."
            className="min-w-0 flex-1 basis-64 rounded-lg border bg-fd-background px-3 py-1.5 text-sm"
            value={value}
            onChange={(e) => {
              setValue(e.target.value);
              setMsg(null);
            }}
          />
          <button
            disabled={busy || value.trim() === saved}
            className="rounded-lg bg-fd-primary px-4 py-1.5 text-sm font-medium text-fd-primary-foreground disabled:opacity-50"
          >
            {busy ? 'שומר...' : 'שמירה'}
          </button>
          {saved && (
            <a
              href={saved}
              target="_blank"
              rel="noreferrer"
              className="rounded-lg px-2 py-1.5 text-sm text-fd-muted-foreground hover:bg-fd-accent"
            >
              פתיחה ב-Drive
            </a>
          )}
        </div>
        {msg && (
          <p role={msg.ok ? 'status' : 'alert'} className={`text-sm ${msg.ok ? 'text-green-600' : 'text-red-600'}`}>
            {msg.text}
          </p>
        )}
      </form>
    </li>
  );
}
