'use client';

import { useEffect, useState } from 'react';
import { CheckCircle2, Circle } from 'lucide-react';
import { createClient } from '@/lib/supabase/client';

const configured = Boolean(process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);

/** Lets a signed-in student mark a lesson as completed. Renders nothing for anonymous visitors. */
export function ProgressToggle({ lesson }: { lesson: string }) {
  const [userId, setUserId] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!configured) return;
    const supabase = createClient();
    (async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) return;
      setUserId(user.id);
      const { data } = await supabase
        .from('lesson_progress')
        .select('lesson_id')
        .eq('student_id', user.id)
        .eq('lesson_id', Number(lesson))
        .maybeSingle();
      setDone(Boolean(data));
    })();
  }, [lesson]);

  if (!userId) return null;

  async function toggle() {
    setBusy(true);
    setError('');
    const supabase = createClient();
    const q = supabase.from('lesson_progress');
    const { error } = done
      ? await q.delete().eq('student_id', userId!).eq('lesson_id', Number(lesson))
      : await q.insert({ student_id: userId, lesson_id: Number(lesson) });
    setBusy(false);
    if (error) return setError('לא הצלחנו לשמור. נסי שוב.');
    setDone(!done);
  }

  return (
    <div>
      <button
        type="button"
        onClick={toggle}
        disabled={busy}
        aria-pressed={done}
        className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors hover:bg-fd-accent disabled:opacity-60"
      >
        {done ? <CheckCircle2 className="size-4 text-green-600" /> : <Circle className="size-4" />}
        {done ? 'השיעור הושלם' : 'סימון השיעור כהושלם'}
      </button>
      {error && (
        <p role="alert" className="mt-1 text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}
