import { AdminNav } from '@/components/admin-nav';
import { createClient, supabaseConfigured } from '@/lib/supabase/server';

export const metadata = { robots: { index: false, follow: false } };

export default async function Layout({ children }: { children: React.ReactNode }) {
  // submissions waiting for a grade, shown on the nav tab (the pages themselves enforce the teacher check)
  let pending = 0;
  if (supabaseConfigured) {
    const supabase = await createClient();
    const { count } = await supabase.from('submissions').select('id', { count: 'exact', head: true }).is('graded_at', null);
    pending = count ?? 0;
  }
  return (
    <>
      <AdminNav pending={pending} />
      {children}
    </>
  );
}
