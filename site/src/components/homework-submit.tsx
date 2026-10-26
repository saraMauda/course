'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { createClient } from '@/lib/supabase/client';

const configured = Boolean(process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);

const MAX_SCREENSHOT = 5 * 1024 * 1024;
const MAX_FILE = 10 * 1024 * 1024;
const REPO_RE = /^https:\/\/(www\.)?(github\.com|gitlab\.com|bitbucket\.org)\/[^\s/]+\/[^\s/]+/i;

interface Assignment {
  id: number;
  due_at: string | null;
}
interface Submission {
  repo_url: string | null;
  screenshot_path: string | null;
  file_path: string | null;
  notes: string | null;
  submitted_at: string;
  grade: number | null;
  feedback: string | null;
  graded_at: string | null;
}

type State =
  | { s: 'loading' }
  | { s: 'anon' }
  | { s: 'no-assignment' }
  | { s: 'ready'; userId: string; assignment: Assignment; submission: Submission | null };

const ext = (f: File) => (f.name.split('.').pop() ?? 'bin').toLowerCase().replace(/[^a-z0-9]/g, '');

export function HomeworkSubmit({ lesson }: { lesson: string }) {
  const [state, setState] = useState<State>({ s: 'loading' });
  const [repo, setRepo] = useState('');
  const [notes, setNotes] = useState('');
  const [screenshot, setScreenshot] = useState<File | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [step, setStep] = useState('');

  useEffect(() => {
    if (!configured) return;
    const supabase = createClient();
    (async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) return setState({ s: 'anon' });
      const { data: assignment } = await supabase
        .from('assignments')
        .select('id, due_at')
        .eq('lesson_id', Number(lesson))
        .eq('kind', 'homework')
        .maybeSingle();
      if (!assignment) return setState({ s: 'no-assignment' });
      const { data: submission } = await supabase
        .from('submissions')
        .select('repo_url, screenshot_path, file_path, notes, submitted_at, grade, feedback, graded_at')
        .eq('assignment_id', assignment.id)
        .eq('student_id', user.id)
        .maybeSingle();
      if (submission) {
        setRepo(submission.repo_url ?? '');
        setNotes(submission.notes ?? '');
      }
      setState({ s: 'ready', userId: user.id, assignment, submission });
    })();
  }, [lesson]);

  if (!configured || state.s === 'loading') return null;

  const box = 'my-8 rounded-xl border bg-fd-card p-5 space-y-4';

  if (state.s === 'anon') {
    return (
      <section className={box}>
        <h2 className="text-xl font-bold">הגשת שיעורי בית</h2>
        <p className="text-fd-muted-foreground">כדי להגיש צריך להתחבר.</p>
        <Link
          href={`/login?next=${encodeURIComponent(`/docs/lessons/lesson-${lesson}/homework`)}`}
          className="inline-block rounded-lg bg-fd-primary px-4 py-2 font-medium text-fd-primary-foreground"
        >
          התחברות
        </Link>
      </section>
    );
  }
  if (state.s === 'no-assignment') return null;

  const { userId, assignment, submission } = state;
  const locked = Boolean(submission?.graded_at);
  const late = assignment.due_at && new Date(assignment.due_at) < new Date();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    if (!REPO_RE.test(repo.trim())) return setError('צריך קישור תקין למאגר, למשל https://github.com/שם/מאגר');
    if (!screenshot && !submission?.screenshot_path) return setError('צריך לצרף צילום מסך');
    if (screenshot && !screenshot.type.startsWith('image/')) return setError('צילום המסך חייב להיות תמונה');
    if (screenshot && screenshot.size > MAX_SCREENSHOT) return setError('צילום המסך גדול מדי (עד 5MB)');
    if (file && file.size > MAX_FILE) return setError('הקובץ גדול מדי (עד 10MB)');
    if (submission && !window.confirm('כבר הוגשה עבודה. לעדכן אותה ולדרוס את הקיים?')) return;

    setBusy(true);
    setDone(false);
    const supabase = createClient();
    const stamp = Date.now();
    const upload = async (f: File, name: string) => {
      setStep(name === 'screenshot' ? 'מעלה צילום מסך...' : 'מעלה קובץ...');
      const p = `${userId}/${assignment.id}/${name}-${stamp}.${ext(f)}`;
      const { error } = await supabase.storage.from('submissions').upload(p, f, { contentType: f.type || undefined });
      if (error) throw error;
      return p;
    };
    try {
      const screenshot_path = screenshot ? await upload(screenshot, 'screenshot') : submission!.screenshot_path;
      const file_path = file ? await upload(file, 'file') : (submission?.file_path ?? null);
      setStep('שומר הגשה...');
      const { error } = await supabase.from('submissions').upsert(
        {
          assignment_id: assignment.id,
          student_id: userId,
          repo_url: repo.trim(),
          screenshot_path,
          file_path,
          notes: notes.trim() || null,
        },
        { onConflict: 'assignment_id,student_id' },
      );
      if (error) throw error;
      setDone(true);
      setState({
        s: 'ready',
        userId,
        assignment,
        submission: {
          repo_url: repo.trim(),
          screenshot_path,
          file_path,
          notes: notes.trim() || null,
          submitted_at: new Date().toISOString(),
          grade: null,
          feedback: null,
          graded_at: null,
        },
      });
      setScreenshot(null);
      setFile(null);
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
      <h2 className="text-xl font-bold">הגשת שיעורי בית</h2>

      {submission && (
        <div className="rounded-lg border bg-fd-background p-3 text-sm space-y-1">
          <div>
            הוגש ב-{new Date(submission.submitted_at).toLocaleString('he-IL')}
            {submission.grade !== null ? ` · ציון ${submission.grade}` : ' · ממתין לבדיקה'}
          </div>
          {submission.feedback && <div>משוב: {submission.feedback}</div>}
        </div>
      )}
      {late && !submission && <p className="text-sm text-amber-600">מועד ההגשה עבר, אפשר עדיין להגיש.</p>}

      {locked ? (
        <p className="text-fd-muted-foreground">ההגשה נבדקה ולכן אי אפשר לשנות אותה.</p>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          <label className="block space-y-1">
            <span className="font-medium">קישור ל-Git</span>
            <input className={input} dir="ltr" type="url" placeholder="https://github.com/user/repo" value={repo} onChange={(e) => setRepo(e.target.value)} required />
          </label>
          <label className="block space-y-1">
            <span className="font-medium">צילום מסך של התוצאה</span>
            <input className={input} type="file" accept="image/*" onChange={(e) => setScreenshot(e.target.files?.[0] ?? null)} />
            {submission?.screenshot_path && !screenshot && (
              <span className="text-xs text-fd-muted-foreground">כבר הועלה צילום. בחרי קובץ רק כדי להחליף.</span>
            )}
          </label>
          <label className="block space-y-1">
            <span className="font-medium">קובץ נוסף (לא חובה)</span>
            <input className={input} type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </label>
          <label className="block space-y-1">
            <span className="font-medium">הערות (לא חובה)</span>
            <textarea className={input} rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
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
          <button disabled={busy} aria-busy={busy} className="rounded-lg bg-fd-primary px-5 py-2 font-medium text-fd-primary-foreground disabled:opacity-60">
            {busy ? 'מעלה...' : submission ? 'עדכון הגשה' : 'הגשה'}
          </button>
        </form>
      )}
    </section>
  );
}
