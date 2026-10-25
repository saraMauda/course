'use client';

import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

export function SignOutButton() {
  const router = useRouter();
  return (
    <button
      onClick={async () => {
        await createClient().auth.signOut();
        router.push('/login');
        router.refresh();
      }}
      className="rounded-lg border px-3 py-1.5 text-sm font-medium hover:bg-fd-accent"
    >
      התנתקות
    </button>
  );
}
