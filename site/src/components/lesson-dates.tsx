'use client';

import { useState } from 'react';
import { createClient } from '@/lib/supabase/client';

export function LessonDates({ lessons }: { lessons: { id: number; title: string; held_on: string | null }[] }) {
  const [dates, setDates] = useState<Record<number, string>>(Object.fromEntries(lessons.map((l) => [l.id, l.held_on ?? ''])));
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  async function save() {
    setBusy(true);
    setMsg(null);
    const supabase = createClient();
    const results = await Promise.all(
      lessons
        .filter((l) => (dates[l.id] || null) !== l.held_on)
        .map((l) => supabase.from('lessons').update({ held_on: dates[l.id] || null }).eq('id', l.id)),
    );
    setBusy(false);
    setMsg(results.some((r) => r.error) ? { ok: false, text: 'השמירה נכשלה' } : { ok: true, text: 'נשמר' });
  }

  return (
    <div className="space-y-4">
      <ul className="divide-y rounded-xl border">
        {lessons.map((l) => (
          <li key={l.id} className="flex flex-wrap items-center justify-between gap-3 p-3">
            <span>
              <span className="font-medium">שיעור {l.id}</span> · {l.title}
            </span>
            <input
              type="date"
              dir="ltr"
              aria-label={`תאריך שיעור ${l.id}`}
              className="rounded-lg border bg-fd-background px-3 py-1.5"
              value={dates[l.id]}
              onChange={(e) => setDates((d) => ({ ...d, [l.id]: e.target.value }))}
            />
          </li>
        ))}
      </ul>
      <div className="flex items-center gap-3">
        <button onClick={save} disabled={busy} className="rounded-lg bg-fd-primary px-4 py-1.5 text-sm font-medium text-fd-primary-foreground disabled:opacity-60">
          שמירת תאריכים
        </button>
        {msg && <span className={`text-sm ${msg.ok ? 'text-green-600' : 'text-red-600'}`}>{msg.text}</span>}
      </div>
    </div>
  );
}
