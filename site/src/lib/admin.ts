import { redirect } from 'next/navigation';
import { createClient, supabaseConfigured } from '@/lib/supabase/server';

/** For admin pages: returns the teacher's Supabase client, or redirects anyone else away. */
export async function requireTeacher() {
  if (!supabaseConfigured) redirect('/dashboard');
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect('/login');
  const { data: me } = await supabase.from('profiles').select('role').eq('id', user.id).single();
  if (me?.role !== 'teacher') redirect('/dashboard');
  return { supabase, user };
}
