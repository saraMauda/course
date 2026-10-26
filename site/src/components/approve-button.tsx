'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

export function ApproveButton({ studentId, approved }: { studentId: string; approved: boolean }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function toggle() {
    if (approved && !window.confirm('לבטל את הגישה של התלמידה לחומרי הקורס?')) return;
    setBusy(true);
    setError('');
    const { error } = await createClient().rpc('approve_student', { student: studentId, ok: !approved });
    setBusy(false);
    if (error) return setError('שגיאה');
    router.refresh();
  }

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={toggle}
        disabled={busy}
        className={`rounded-lg px-3 py-1 text-sm font-medium disabled:opacity-60 ${
          approved ? 'border hover:bg-fd-accent' : 'bg-fd-primary text-fd-primary-foreground'
        }`}
      >
        {approved ? 'ביטול אישור' : 'אישור'}
      </button>
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  );
}
