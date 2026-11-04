'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import { addDays, weeklyDates } from '@/lib/dates';
import { daysBetween, todayInIsrael } from '@/lib/reminders';

interface Lesson {
  id: number;
  title: string;
  held_on: string | null;
}

const weekday = (d: string) => new Date(`${d}T12:00:00Z`).toLocaleDateString('he-IL', { weekday: 'long', timeZone: 'Asia/Jerusalem' });

export function LessonDates({ lessons }: { lessons: Lesson[] }) {
  const router = useRouter();
  const [dates, setDates] = useState<Record<number, string>>(Object.fromEntries(lessons.map((l) => [l.id, l.held_on ?? ''])));
  const [start, setStart] = useState('');
  const [step, setStep] = useState(7);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const today = todayInIsrael();
  const changed = lessons.filter((l) => (dates[l.id] || null) !== l.held_on);
  const nextId = lessons.find((l) => dates[l.id] && daysBetween(today, dates[l.id]) >= 0)?.id;

  function fillWeekly() {
    if (!start) return setMsg({ ok: false, text: 'בחרי קודם תאריך לשיעור הראשון' });
    const filled = weeklyDates(start, lessons.length, step);
    setDates(Object.fromEntries(lessons.map((l, i) => [l.id, filled[i]])));
    setMsg(null);
  }

  // push this lesson and every later dated lesson back by a week (a holiday, a missed class)
  function postponeFrom(id: number) {
    setDates((d) => Object.fromEntries(lessons.map((l) => [l.id, l.id >= id && d[l.id] ? addDays(d[l.id], 7) : d[l.id]])));
  }

  async function save() {
    setBusy(true);
    setMsg(null);
    const supabase = createClient();
    const results = await Promise.all(
      changed.map((l) => supabase.from('lessons').update({ held_on: dates[l.id] || null }).eq('id', l.id)),
    );
    setBusy(false);
    if (results.some((r) => r.error)) return setMsg({ ok: false, text: 'השמירה נכשלה' });
    setMsg({ ok: true, text: `נשמר (${changed.length} שינויים)` });
    router.refresh();
  }

  const input = 'rounded-lg border bg-fd-background px-3 py-1.5 text-sm';
  return (
    <div className="space-y-4">
      <section className="space-y-2 rounded-xl border p-4" aria-label="מילוי תאריכים אוטומטי">
        <h2 className="font-semibold">מילוי מהיר</h2>
        <p className="text-sm text-fd-muted-foreground">מזינות את התאריך של שיעור 1, והאתר ממלא את כל השאר לפי הקפיצה. אחר כך אפשר לתקן שיעור בודד.</p>
        <div className="flex flex-wrap items-end gap-3">
          <label className="space-y-1 text-sm">
            <span className="block">תאריך שיעור 1</span>
            <input type="date" dir="ltr" className={input} value={start} onChange={(e) => setStart(e.target.value)} />
          </label>
          <label className="space-y-1 text-sm">
            <span className="block">כל כמה ימים</span>
            <select className={input} value={step} onChange={(e) => setStep(Number(e.target.value))}>
              <option value={7}>כל שבוע</option>
              <option value={14}>כל שבועיים</option>
              <option value={1}>כל יום</option>
            </select>
          </label>
          <button type="button" onClick={fillWeekly} className="rounded-lg border px-3 py-1.5 text-sm font-medium hover:bg-fd-accent">
            מילוי כל השיעורים
          </button>
          <button
            type="button"
            onClick={() => setDates(Object.fromEntries(lessons.map((l) => [l.id, ''])))}
            className="rounded-lg px-3 py-1.5 text-sm text-fd-muted-foreground hover:bg-fd-accent"
          >
            ניקוי הכול
          </button>
        </div>
      </section>

      <ul className="divide-y rounded-xl border">
        {lessons.map((l, i) => {
          const d = dates[l.id];
          const prev = lessons[i - 1] && dates[lessons[i - 1].id];
          const outOfOrder = d && prev && d <= prev;
          const diff = d ? daysBetween(today, d) : null;
          return (
            <li key={l.id} className={`flex flex-wrap items-center justify-between gap-3 p-3 ${l.id === nextId ? 'bg-fd-primary/5' : ''}`}>
              <span className="min-w-0">
                <span className="font-medium">שיעור {l.id}</span> · {l.title}
                {l.id === nextId && <span className="ms-2 rounded-full bg-fd-primary px-2 py-0.5 text-xs text-fd-primary-foreground">הבא</span>}
                {diff !== null && diff < 0 && <span className="ms-2 text-xs text-fd-muted-foreground">התקיים</span>}
                {outOfOrder && <span className="ms-2 text-xs text-red-600">התאריך לא אחרי השיעור הקודם</span>}
              </span>
              <span className="flex items-center gap-2">
                {d && <span className="text-sm text-fd-muted-foreground">{weekday(d)}</span>}
                <input
                  type="date"
                  dir="ltr"
                  aria-label={`תאריך שיעור ${l.id}`}
                  className={input}
                  value={d}
                  onChange={(e) => setDates((s) => ({ ...s, [l.id]: e.target.value }))}
                />
                <button
                  type="button"
                  disabled={!d}
                  onClick={() => postponeFrom(l.id)}
                  title="דוחה את השיעור הזה ואת כל מה שאחריו בשבוע"
                  className="rounded-lg px-2 py-1 text-xs text-fd-muted-foreground hover:bg-fd-accent disabled:opacity-40"
                >
                  דחייה בשבוע
                </button>
              </span>
            </li>
          );
        })}
      </ul>

      <div className="sticky bottom-3 flex items-center gap-3 rounded-xl border bg-fd-background p-3 shadow-sm">
        <button
          onClick={save}
          disabled={busy || changed.length === 0}
          className="rounded-lg bg-fd-primary px-4 py-1.5 text-sm font-medium text-fd-primary-foreground disabled:opacity-50"
        >
          {busy ? 'שומרת...' : 'שמירת תאריכים'}
        </button>
        <span className="text-sm text-fd-muted-foreground">{changed.length > 0 ? `${changed.length} שינויים שלא נשמרו` : 'הכול שמור'}</span>
        {msg && <span className={`text-sm ${msg.ok ? 'text-green-600' : 'text-red-600'}`}>{msg.text}</span>}
      </div>
    </div>
  );
}
