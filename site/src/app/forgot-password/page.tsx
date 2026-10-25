'use client';

import Link from 'next/link';
import { useState } from 'react';
import { createClient } from '@/lib/supabase/client';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError('');
    const { error } = await createClient().auth.resetPasswordForEmail(email.trim(), {
      redirectTo: `${window.location.origin}/auth/callback?next=/reset-password`,
    });
    setBusy(false);
    if (error) {
      return setError(
        error.status === 429
          ? 'נשלחו יותר מדי מיילים. נסי שוב בעוד זמן מה, או פני למרצה לאיפוס ידני.'
          : 'לא הצלחנו לשלוח מייל. נסי שוב.',
      );
    }
    // same answer whether or not the address has an account, so nobody can probe which emails are registered
    setSent(true);
  }

  return (
    <main className="flex-1 flex items-center justify-center p-6">
      <form onSubmit={submit} className="w-full max-w-sm space-y-4 rounded-xl border p-6">
        <h1 className="text-2xl font-bold">איפוס סיסמה</h1>
        {sent ? (
          <p className="text-sm text-green-600">
            אם קיים חשבון עם הכתובת הזו, נשלח אליה קישור לבחירת סיסמה חדשה. כדאי לבדוק גם בתיקיית הספאם.
          </p>
        ) : (
          <>
            <p className="text-sm text-fd-muted-foreground">נשלח קישור לבחירת סיסמה חדשה לכתובת המייל שלך.</p>
            <input
              className="w-full rounded-lg border bg-fd-background px-3 py-2"
              type="email"
              dir="ltr"
              placeholder="אימייל"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button disabled={busy} className="w-full rounded-lg bg-fd-primary py-2 font-medium text-fd-primary-foreground disabled:opacity-60">
              {busy ? 'שולח...' : 'שליחת קישור'}
            </button>
          </>
        )}
        <Link href="/login" className="block text-sm underline">
          חזרה להתחברות
        </Link>
      </form>
    </main>
  );
}
