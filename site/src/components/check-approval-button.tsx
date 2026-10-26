'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

/** Refreshes the session (so the new approval reaches the token) and retries the dashboard. */
export function CheckApprovalButton() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');

  async function check() {
    setBusy(true);
    setMsg('');
    const supabase = createClient();
    await supabase.auth.refreshSession();
    const {
      data: { user },
    } = await supabase.auth.getUser();
    const { data } = user
      ? await supabase.from('profiles').select('approved, role').eq('id', user.id).maybeSingle()
      : { data: null };
    setBusy(false);
    if (data?.approved || data?.role === 'teacher') {
      router.push('/dashboard');
      router.refresh();
    } else {
      setMsg('עדיין לא אושר. נסי שוב מאוחר יותר.');
    }
  }

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={check}
        disabled={busy}
        className="rounded-lg bg-fd-primary px-4 py-2 text-sm font-medium text-fd-primary-foreground disabled:opacity-60"
      >
        {busy ? 'בודקת...' : 'בדיקת סטטוס אישור'}
      </button>
      {msg && (
        <p role="status" className="text-sm text-fd-muted-foreground">
          {msg}
        </p>
      )}
    </div>
  );
}
