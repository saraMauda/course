'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

export function GradeForm({
  submissionId,
  grade,
  feedback,
  graded,
}: {
  submissionId: number;
  grade: number | null;
  feedback: string | null;
  graded: boolean;
}) {
  const router = useRouter();
  const [g, setG] = useState(grade === null ? '' : String(grade));
  const [fb, setFb] = useState(feedback ?? '');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const [notify, setNotify] = useState(true);

  async function run(update: Record<string, unknown>, okText: string, event: 'returned' | 'graded') {
    setBusy(true);
    setMsg(null);
    const { error } = await createClient().from('submissions').update(update).eq('id', submissionId);
    if (error) {
      setBusy(false);
      return setMsg({ ok: false, text: 'השמירה נכשלה' });
    }
    let text = okText;
    if (notify) {
      const res = await fetch('/api/notify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ submissionId, event }),
      }).catch(() => null);
      text += res?.ok ? ' · נשלח מייל' : ' · שליחת המייל נכשלה';
    }
    setBusy(false);
    setMsg({ ok: true, text });
    router.refresh();
  }

  function save(value: number) {
    return run(
      { grade: value, feedback: fb.trim() || null, graded_at: new Date().toISOString() },
      'נשמר',
      'graded',
    );
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const n = Number(g);
    if (g.trim() === '' || !Number.isFinite(n) || n < 0 || n > 100) {
      return setMsg({ ok: false, text: 'ציון חייב להיות בין 0 ל-100' });
    }
    save(n);
  }

  const input = 'rounded-lg border bg-fd-background px-3 py-1.5';
  return (
    <form onSubmit={submit} className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <input
          className={`${input} w-24`}
          type="number"
          min={0}
          max={100}
          step="0.5"
          dir="ltr"
          placeholder="ציון"
          value={g}
          onChange={(e) => setG(e.target.value)}
        />
        <button type="button" disabled={busy} onClick={() => { setG('100'); save(100); }} className="rounded-lg border px-3 py-1.5 text-sm hover:bg-fd-accent disabled:opacity-60">
          מאושר (100)
        </button>
        <button disabled={busy} className="rounded-lg bg-fd-primary px-4 py-1.5 text-sm font-medium text-fd-primary-foreground disabled:opacity-60">
          שמירת ציון
        </button>
        {graded && (
          <button
            type="button"
            disabled={busy}
            onClick={() => run({ grade: null, graded_at: null, feedback: fb.trim() || null }, 'הוחזר לתיקון', 'returned')}
            className="rounded-lg border border-amber-500 px-3 py-1.5 text-sm text-amber-700 hover:bg-amber-500/10 disabled:opacity-60"
          >
            החזרה לתיקון
          </button>
        )}
        {msg && <span className={`text-sm ${msg.ok ? 'text-green-600' : 'text-red-600'}`}>{msg.text}</span>}
      </div>
      <textarea
        className={`${input} w-full`}
        rows={2}
        placeholder="משוב לתלמידה (לא חובה)"
        value={fb}
        onChange={(e) => setFb(e.target.value)}
      />
      <label className="flex cursor-pointer items-center gap-2 text-sm text-fd-muted-foreground">
        <input type="checkbox" checked={notify} onChange={(e) => setNotify(e.target.checked)} />
        שליחת מייל לתלמידה
      </label>
    </form>
  );
}
