import { NextResponse } from 'next/server';
import { createServiceClient, serviceConfigured } from '@/lib/supabase/admin';
import { buildReminderMail, sendMail, smtpConfigured } from '@/lib/mailer';
import { planReminders, todayInIsrael, type Assignment, type Lesson, type Student } from '@/lib/reminders';

// Called once a day by Vercel Cron (see vercel.json). Vercel sends `Authorization: Bearer $CRON_SECRET`.
// `?dry=1` lists what would be sent without sending or recording anything.
export async function GET(request: Request) {
  const secret = process.env.CRON_SECRET;
  if (!secret || request.headers.get('authorization') !== `Bearer ${secret}`) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }
  if (!serviceConfigured) return NextResponse.json({ error: 'SUPABASE_SERVICE_ROLE_KEY is not set' }, { status: 503 });
  const dry = new URL(request.url).searchParams.get('dry') === '1';
  if (!dry && !smtpConfigured) return NextResponse.json({ error: 'SMTP is not configured' }, { status: 503 });

  const db = createServiceClient();
  const today = todayInIsrael();

  const [{ data: lessons }, { data: assignments }, { data: profiles }, { data: subs }, { data: log }] = await Promise.all([
    db.from('lessons').select('id, title, held_on').not('held_on', 'is', null),
    db.from('assignments').select('id, lesson_id, kind, title'),
    db.from('profiles').select('id, full_name').eq('role', 'student').eq('approved', true),
    db.from('submissions').select('student_id, assignment_id'),
    db.from('reminder_log').select('student_id, kind, ref_id'),
  ]);

  // emails live in auth.users; paginate through all of them
  const emails = new Map<string, string>();
  for (let page = 1; ; page++) {
    const { data, error } = await db.auth.admin.listUsers({ page, perPage: 200 });
    if (error) return NextResponse.json({ error: 'could not list users' }, { status: 500 });
    for (const u of data.users) if (u.email) emails.set(u.id, u.email);
    if (data.users.length < 200) break;
  }
  const students: Student[] = (profiles ?? [])
    .filter((p) => emails.has(p.id))
    .map((p) => ({ id: p.id, full_name: p.full_name, email: emails.get(p.id)! }));

  const plan = planReminders({
    today,
    lessons: (lessons ?? []) as Lesson[],
    assignments: (assignments ?? []) as Assignment[],
    students,
    submitted: new Set((subs ?? []).map((s) => `${s.student_id}:${s.assignment_id}`)),
    already: new Set((log ?? []).map((l) => `${l.student_id}:${l.kind}:${l.ref_id}`)),
  });

  if (dry) {
    return NextResponse.json({
      today,
      would_send: plan.map((r) => ({ to: r.student.full_name, kind: r.kind, assignment: r.assignment?.title, lesson: r.lesson.id })),
    });
  }

  const link = `${new URL(request.url).origin}/dashboard`;
  let sent = 0;
  let failed = 0;
  for (const r of plan) {
    try {
      await sendMail(
        r.student.email,
        buildReminderMail({
          kind: r.kind,
          studentName: r.student.full_name,
          lessonTitle: r.lesson.title,
          lessonDate: r.lesson.held_on!,
          assignmentTitle: r.assignment?.title,
          link,
        }),
      );
      await db.from('reminder_log').upsert({ student_id: r.student.id, kind: r.kind, ref_id: r.refId });
      sent++;
    } catch (err) {
      failed++;
      console.error('reminders: send failed', r.kind, r.refId, err);
    }
  }
  return NextResponse.json({ today, sent, failed });
}
