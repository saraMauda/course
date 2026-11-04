import { NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { buildCustomMail, sendMail, smtpConfigured } from '@/lib/mailer';
import { renderTemplate, unknownPlaceholders } from '@/lib/email-templates';
import { loadMailContext, originOf } from '@/lib/email-data';

const MAX_RECIPIENTS = 200;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

// Teacher-only: sends one template to the chosen students, filling the placeholders for each of them.
export async function POST(request: Request) {
  const input = (await request.json().catch(() => null)) as { ids?: unknown; subject?: unknown; body?: unknown } | null;
  const ids = Array.isArray(input?.ids) ? [...new Set(input.ids.filter((x): x is string => typeof x === 'string' && UUID.test(x)))] : [];
  const subject = typeof input?.subject === 'string' ? input.subject.trim() : '';
  const body = typeof input?.body === 'string' ? input.body : '';
  if (!ids.length || ids.length > MAX_RECIPIENTS || !subject || !body.trim() || subject.length > 200 || body.length > 10_000) {
    return NextResponse.json({ error: 'bad request' }, { status: 400 });
  }
  const unknown = unknownPlaceholders(subject + '\n' + body);
  if (unknown.length) return NextResponse.json({ error: `unknown placeholders: ${unknown.join(', ')}` }, { status: 400 });

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  const { data: me } = await supabase.from('profiles').select('role').eq('id', user.id).single();
  if (me?.role !== 'teacher') return NextResponse.json({ error: 'forbidden' }, { status: 403 });
  if (!smtpConfigured) return NextResponse.json({ error: 'SMTP is not configured' }, { status: 503 });

  const [{ students }, { data: emails }] = await Promise.all([
    loadMailContext(supabase, `${originOf(request.headers)}/dashboard`, ids),
    supabase.rpc('student_emails', { ids }),
  ]);
  const emailOf = new Map<string, string>((emails ?? []).map((e: { id: string; email: string }) => [e.id, e.email]));

  const failed: { name: string; reason: string }[] = [];
  const log: { student_id: string; subject: string; body: string; status: 'sent' | 'failed' }[] = [];
  let sent = 0;
  for (const s of students) {
    const filledSubject = renderTemplate(subject, s.vars);
    const filledBody = renderTemplate(body, s.vars);
    const to = emailOf.get(s.id);
    let status: 'sent' | 'failed' = 'sent';
    if (!to) {
      status = 'failed';
      failed.push({ name: s.full_name || 'ללא שם', reason: 'אין כתובת מייל' });
    } else {
      try {
        await sendMail(to, buildCustomMail(filledSubject, filledBody));
        sent++;
      } catch (err) {
        console.error('email: send failed', s.id, err);
        status = 'failed';
        failed.push({ name: s.full_name || 'ללא שם', reason: 'השליחה נכשלה' });
      }
    }
    log.push({ student_id: s.id, subject: filledSubject, body: filledBody, status });
  }
  if (log.length) {
    const { error } = await supabase.from('email_log').insert(log);
    if (error) console.error('email: could not write log', error);
  }
  return NextResponse.json({ sent, failed });
}
