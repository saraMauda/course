'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError('');
    const supabase = createClient();
    const { error } =
      mode === 'login'
        ? await supabase.auth.signInWithPassword({ email, password })
        : await supabase.auth.signUp({ email, password, options: { data: { full_name: fullName } } });
    setBusy(false);
    if (error) return setError(error.message);
    const next = new URLSearchParams(window.location.search).get('next');
    router.push(next && next.startsWith('/') && !next.startsWith('//') ? next : '/dashboard');
    router.refresh();
  }

  const input = 'w-full rounded-lg border bg-fd-background px-3 py-2';
  return (
    <main className="flex-1 flex items-center justify-center p-6">
      <form onSubmit={submit} className="w-full max-w-sm space-y-4 rounded-xl border p-6">
        <h1 className="text-2xl font-bold">{mode === 'login' ? 'התחברות' : 'הרשמה'}</h1>
        {mode === 'signup' && (
          <input className={input} placeholder="שם מלא" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
        )}
        <input className={input} type="email" dir="ltr" placeholder="אימייל" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input className={input} type="password" dir="ltr" placeholder="סיסמה" minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} required />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button disabled={busy} className="w-full rounded-lg bg-fd-primary text-fd-primary-foreground py-2 font-medium disabled:opacity-60">
          {mode === 'login' ? 'כניסה' : 'יצירת חשבון'}
        </button>
        <button type="button" className="text-sm underline" onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}>
          {mode === 'login' ? 'אין לי חשבון עדיין' : 'כבר יש לי חשבון'}
        </button>
      </form>
    </main>
  );
}
