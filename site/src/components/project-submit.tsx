'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { createClient } from '@/lib/supabase/client';
import { projectItems } from '@/lib/project-items';

const configured = Boolean(process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);
const MAX_FILE = 10 * 1024 * 1024;

type Stored = { text?: string; path?: string };
type Items = Record<string, Stored>;
interface Submission {
  id: number;
  items: Items;
  notes: string | null;
  submitted_at: string;
  grade: number | null;
  feedback: string | null;
  graded_at: string | null;
}
type State =
  | { s: 'loading' }
  | { s: 'anon' }
  | { s: 'ready'; userId: string; submission: Submission | null; checks: Record<string, boolean> };

const ext = (f: File) => (f.name.split('.').pop() ?? 'bin').toLowerCase().replace(/[^a-z0-9]/g, '');

export function ProjectSubmit({ n }: { n: number }) {
  const project = projectItems[n];
  const [state, setState] = useState<State>({ s: 'loading' });
  const [texts, setTexts] = useState<Record<string, string>>({});
  const [files, setFiles] = useState<Record<string, File | null>>({});
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [step, setStep] = useState('');

  useEffect(() => {
    if (!configured || !project) return;
    const supabase = createClient();
    (async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) return setState({ s: 'anon' });
      const { data: sub } = await supabase
        .from('submissions')
        .select('id, items, notes, submitted_at, grade, feedback, graded_at')
        .eq('assignment_id', project.assignmentId)
        .eq('student_id', user.id)
        .maybeSingle();
      const checks: Record<string, boolean> = {};
      if (sub) {
        const { data } = await supabase.from('submission_checks').select('item_key, ok').eq('submission_id', sub.id);
        for (const c of data ?? []) checks[c.item_key] = c.ok;
        setTexts(Object.fromEntries(Object.entries((sub.items ?? {}) as Items).map(([k, v]) => [k, v.text ?? ''])));
        setNotes(sub.notes ?? '');
      }
      setState({ s: 'ready', userId: user.id, submission: sub as Submission | null, checks });
    })();
  }, [project]);

  if (!configured || !project || state.s === 'loading') return null;

  const box = 'my-8 rounded-xl border bg-fd-card p-5 space-y-4';
  if (state.s === 'anon') {
    return (
      <section className={box}>
        <h2 className="text-xl font-bold">הגשת {project.title}</h2>
        <p className="text-fd-muted-foreground">כדי להגיש צריך להתחבר.</p>
        <Link
          href={`/login?next=${encodeURIComponent(`/docs/projects/project-0${n}`)}`}
          className="inline-block rounded-lg bg-fd-primary px-4 py-2 font-medium text-fd-primary-foreground"
        >
          התחברות
        </Link>
      </section>
    );
  }

  const { userId, submission, checks } = state;
  const locked = Boolean(submission?.graded_at);
  const stored = submission?.items ?? {};

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    for (const it of project.items) {
      const text = (texts[it.key] ?? '').trim();
      const has = it.kind === 'file' ? files[it.key] || stored[it.key]?.path : text;
      if (!has && !it.optional) return setError(`חסר: ${it.label}`);
      if (it.kind === 'link' && text && !/^https?:\/\//i.test(text)) return setError(`צריך קישור תקין (https://...) ב: ${it.label}`);
      if (files[it.key] && files[it.key]!.size > MAX_FILE) return setError(`הקובץ גדול מדי (עד 10MB): ${it.label}`);
    }

    if (submission && !window.confirm('כבר הוגשה עבודה. לעדכן אותה ולדרוס את הקיים?')) return;

    setBusy(true);
    setDone(false);
    const supabase = createClient();
    const stamp = Date.now();
    try {
      const items: Items = {};
      for (const it of project.items) {
        const text = (texts[it.key] ?? '').trim();
        if (it.kind === 'file') {
          const f = files[it.key];
          let path = stored[it.key]?.path;
          if (f) {
            setStep(`מעלה: ${it.label.slice(0, 40)}...`);
            path = `${userId}/${project.assignmentId}/${it.key}-${stamp}.${ext(f)}`;
            const { error } = await supabase.storage.from('submissions').upload(path, f, { contentType: f.type || undefined });
            if (error) throw error;
          }
          items[it.key] = { ...(path ? { path } : {}), ...(text ? { text } : {}) };
        } else {
          items[it.key] = { text };
        }
      }
      setStep('שומר הגשה...');
      const { data, error } = await supabase
        .from('submissions')
        .upsert(
          {
            assignment_id: project.assignmentId,
            student_id: userId,
            repo_url: items.repo?.text || null,
            items,
            notes: notes.trim() || null,
          },
          { onConflict: 'assignment_id,student_id' },
        )
        .select('id, items, notes, submitted_at, grade, feedback, graded_at')
        .single();
      if (error) throw error;
      setDone(true);
      setFiles({});
      setState({ s: 'ready', userId, submission: data as Submission, checks });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'ההגשה נכשלה, נסי שוב');
    } finally {
      setBusy(false);
      setStep('');
    }
  }

  const input = 'w-full rounded-lg border bg-fd-background px-3 py-2';
  return (
    <section className={box}>
      <h2 className="text-xl font-bold">הגשת {project.title}</h2>

      {submission && (
        <div className="rounded-lg border bg-fd-background p-3 text-sm space-y-1">
          <div>
            הוגש ב-{new Date(submission.submitted_at).toLocaleString('he-IL')}
            {submission.grade !== null ? ` · ציון ${submission.grade}` : ' · ממתין לבדיקה'}
          </div>
          {submission.feedback && <div>משוב: {submission.feedback}</div>}
        </div>
      )}
      {locked && <p className="text-fd-muted-foreground">ההגשה נבדקה ולכן אי אפשר לשנות אותה.</p>}

      <form onSubmit={submit} className="space-y-4">
        <ol className="space-y-4">
          {project.items.map((it, i) => (
            <li key={it.key} className="space-y-1.5 rounded-lg border bg-fd-background p-3">
              <div className="flex items-start justify-between gap-2">
                <span className="font-medium">
                  {i + 1}. {it.label}
                  {it.optional && <span className="text-fd-muted-foreground"> (לא חובה)</span>}
                </span>
                {submission && checks[it.key] !== undefined && (
                  <span className={`shrink-0 text-sm ${checks[it.key] ? 'text-green-600' : 'text-amber-600'}`}>
                    {checks[it.key] ? '✔ אושר' : 'לתיקון'}
                  </span>
                )}
              </div>
              {it.kind === 'file' && (
                <>
                  <input
                    className={input}
                    type="file"
                    aria-label={`קובץ עבור: ${it.label}`}
                    disabled={locked}
                    onChange={(e) => setFiles({ ...files, [it.key]: e.target.files?.[0] ?? null })}
                  />
                  {stored[it.key]?.path && !files[it.key] && (
                    <span className="text-xs text-fd-muted-foreground">כבר הועלה קובץ. בחרי קובץ רק כדי להחליף.</span>
                  )}
                </>
              )}
              {it.kind === 'file' ? (
                <input
                  className={input}
                  aria-label={`הערה או קישור עבור: ${it.label}`}
                  placeholder="הערה או קישור (לא חובה)"
                  disabled={locked}
                  value={texts[it.key] ?? ''}
                  onChange={(e) => setTexts({ ...texts, [it.key]: e.target.value })}
                />
              ) : (
                <textarea
                  className={input}
                  aria-label={it.label}
                  rows={it.kind === 'link' ? 1 : 3}
                  dir={it.kind === 'link' ? 'ltr' : undefined}
                  placeholder={it.kind === 'link' ? 'https://...' : 'כתבי כאן'}
                  disabled={locked}
                  value={texts[it.key] ?? ''}
                  onChange={(e) => setTexts({ ...texts, [it.key]: e.target.value })}
                />
              )}
            </li>
          ))}
        </ol>
        <label className="block space-y-1">
          <span className="font-medium">הערות (לא חובה)</span>
          <textarea className={input} rows={3} disabled={locked} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </label>
        {error && (
          <p role="alert" className="text-sm text-red-600">
            {error}
          </p>
        )}
        {done && (
          <p role="status" className="text-sm text-green-600">
            ההגשה נשמרה.
          </p>
        )}
        {busy && step && (
          <p role="status" className="text-sm text-fd-muted-foreground">
            {step}
          </p>
        )}
        {!locked && (
          <button disabled={busy} aria-busy={busy} className="rounded-lg bg-fd-primary px-5 py-2 font-medium text-fd-primary-foreground disabled:opacity-60">
            {busy ? 'מעלה...' : submission ? 'עדכון הגשה' : 'הגשה'}
          </button>
        )}
      </form>
    </section>
  );
}
