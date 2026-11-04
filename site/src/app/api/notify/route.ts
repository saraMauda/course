import { NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { buildSubmissionMail, sendMail, smtpConfigured, type SubmissionEvent } from '@/lib/mailer';

// Teacher-only: emails a student about one of her submissions (returned for fixes / graded).
export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as { submissionId?: unknown; event?: unknown } | null;
  const submissionId = Number(body?.submissionId);
  const event = body?.event as SubmissionEvent;
  if (!Number.isInteger(submissionId) || (event !== 'returned' && event !== 'graded')) {
    return NextResponse.json({ error: 'bad request' }, { status: 400 });
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  const { data: me } = await supabase.from('profiles').select('role').eq('id', user.id).single();
  if (me?.role !== 'teacher') return NextResponse.json({ error: 'forbidden' }, { status: 403 });

  if (!smtpConfigured) return NextResponse.json({ error: 'SMTP is not configured' }, { status: 503 });

  const { data: sub } = await supabase
    .from('submissions')
    .select('student_id, grade, feedback, assignments(title)')
    .eq('id', submissionId)
    .single();
  if (!sub) return NextResponse.json({ error: 'not found' }, { status: 404 });

  const [{ data: email }, { data: student }] = await Promise.all([
    supabase.rpc('student_email', { student: sub.student_id }),
    supabase.from('profiles').select('full_name').eq('id', sub.student_id).single(),
  ]);
  if (!email) return NextResponse.json({ error: 'student email not found' }, { status: 404 });

  const assignment = sub.assignments as unknown as { title: string } | null;
  const mail = buildSubmissionMail({
    event,
    studentName: student?.full_name ?? '',
    assignmentTitle: assignment?.title ?? 'משימה',
    grade: sub.grade,
    feedback: sub.feedback,
    link: `${new URL(request.url).origin}/dashboard`,
  });

  try {
    await sendMail(email, mail);
  } catch (err) {
    console.error('notify: send failed', err);
    return NextResponse.json({ error: 'send failed' }, { status: 502 });
  }
  return NextResponse.json({ ok: true });
}
