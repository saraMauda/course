import type { createClient } from '@/lib/supabase/server';
import { studentVars, type Vars } from '@/lib/email-templates';
import { todayInIsrael } from '@/lib/reminders';

type Supabase = Awaited<ReturnType<typeof createClient>>;

export interface MailStudent {
  id: string;
  full_name: string;
  approved: boolean;
  /** ids of the assignments this student already submitted */
  submitted: number[];
  vars: Vars;
}

/** Students plus the per-student placeholder values, shared by the composer page and the send route. */
export async function loadMailContext(supabase: Supabase, link: string, ids?: string[]) {
  let profiles = supabase.from('profiles').select('id, full_name, approved').eq('role', 'student').order('full_name');
  if (ids) profiles = profiles.in('id', ids);
  const [{ data: people }, { data: lessons }, { data: assignments }, { data: subs }] = await Promise.all([
    profiles,
    supabase.from('lessons').select('id, title, held_on').order('id'),
    supabase.from('assignments').select('id, lesson_id, title, due_at').order('id'),
    supabase.from('submissions').select('student_id, assignment_id'),
  ]);

  const today = todayInIsrael();
  const now = new Date();
  const submittedBy = new Map<string, Set<number>>();
  for (const s of subs ?? []) {
    if (!submittedBy.has(s.student_id)) submittedBy.set(s.student_id, new Set());
    submittedBy.get(s.student_id)!.add(s.assignment_id);
  }

  const students: MailStudent[] = (people ?? []).map((p) => {
    const submitted = submittedBy.get(p.id) ?? new Set<number>();
    return {
      id: p.id,
      full_name: p.full_name,
      approved: p.approved,
      submitted: [...submitted],
      vars: studentVars({ name: p.full_name, today, now, lessons: lessons ?? [], assignments: assignments ?? [], submitted, link }),
    };
  });
  return { students, assignments: assignments ?? [] };
}

/** `https://host` of the current request, for links inside emails. */
export function originOf(h: Headers) {
  const host = h.get('x-forwarded-host') ?? h.get('host') ?? 'localhost:3000';
  const proto = h.get('x-forwarded-proto') ?? (host.startsWith('localhost') ? 'http' : 'https');
  return `${proto}://${host}`;
}
