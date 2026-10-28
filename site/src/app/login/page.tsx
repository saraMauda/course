'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError('');
    const supabase = createClient();
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setBusy(false);
    if (error) {
      if (error.status === 429) return setError('בוצעו יותר מדי ניסיונות. נסי שוב בעוד כמה דקות.');
      return setError('אימייל או סיסמה שגויים');
    }
    const next = new URLSearchParams(window.location.search).get('next');
    router.push(next && next.startsWith('/') && !next.startsWith('//') ? next : '/dashboard');
    router.refresh();
  }

  const input = 'w-full rounded-lg border bg-fd-background px-3 py-2';
  return (
    <main className="flex-1 flex items-center justify-center p-6">
      <form onSubmit={submit} className="w-full max-w-sm space-y-4 rounded-xl border p-6">
        <h1 className="text-2xl font-bold">התחברות</h1>
        <input className={input} type="email" dir="ltr" aria-label="אימייל" autoComplete="email" placeholder="אימייל" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input className={input} type="password" dir="ltr" aria-label="סיסמה" autoComplete="current-password" placeholder="סיסמה" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} required />
        {error && (
          <p role="alert" className="text-sm text-red-600">
            {error}
          </p>
        )}
        <button disabled={busy} className="w-full rounded-lg bg-fd-primary text-fd-primary-foreground py-2 font-medium disabled:opacity-60">
          כניסה
        </button>
        <Link href="/forgot-password" className="block text-sm underline">
          שכחתי סיסמה
        </Link>
      </form>
    </main>
  );
}
