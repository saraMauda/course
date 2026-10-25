'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

export default function ResetPasswordPage() {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    if (password.length < 8) return setError('הסיסמה חייבת להכיל 8 תווים לפחות');
    if (password !== confirm) return setError('הסיסמאות אינן זהות');
    setBusy(true);
    const { error } = await createClient().auth.updateUser({ password });
    setBusy(false);
    if (error) return setError('לא הצלחנו לעדכן את הסיסמה. ייתכן שהקישור פג, נסי לבקש קישור חדש.');
    router.push('/dashboard');
    router.refresh();
  }

  const input = 'w-full rounded-lg border bg-fd-background px-3 py-2';
  return (
    <main className="flex-1 flex items-center justify-center p-6">
      <form onSubmit={submit} className="w-full max-w-sm space-y-4 rounded-xl border p-6">
        <h1 className="text-2xl font-bold">בחירת סיסמה חדשה</h1>
        <input className={input} type="password" dir="ltr" placeholder="סיסמה חדשה" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} required />
        <input className={input} type="password" dir="ltr" placeholder="אימות סיסמה" minLength={8} value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button disabled={busy} className="w-full rounded-lg bg-fd-primary py-2 font-medium text-fd-primary-foreground disabled:opacity-60">
          {busy ? 'שומר...' : 'שמירה'}
        </button>
      </form>
    </main>
  );
}
