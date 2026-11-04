import { headers } from 'next/headers';
import { requireTeacher } from '@/lib/admin';
import { EmailComposer } from '@/components/email-composer';
import { loadMailContext, originOf } from '@/lib/email-data';
import { smtpConfigured } from '@/lib/mailer';

export const metadata = { title: 'מיילים' };

const dateFmt = new Intl.DateTimeFormat('he-IL', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Jerusalem' });

export default async function EmailPage({ searchParams }: { searchParams: Promise<{ to?: string; template?: string }> }) {
  const { supabase } = await requireTeacher();
  const { to, template } = await searchParams;

  const origin = originOf(await headers());
  const [{ students, assignments }, templates, log] = await Promise.all([
    loadMailContext(supabase, `${origin}/dashboard`),
    supabase.from('email_templates').select('id, name, subject, body').order('created_at', { ascending: false }),
    supabase.from('email_log').select('id, student_id, subject, status, sent_at').order('sent_at', { ascending: false }).limit(30),
  ]);
  const nameOf = new Map(students.map((s) => [s.id, s.full_name || 'ללא שם']));

  return (
    <main className="mx-auto max-w-5xl space-y-6 p-4 sm:p-6">
      <div>
        <h1 className="text-2xl font-bold">מיילים לתלמידות</h1>
        <p className="text-sm text-fd-muted-foreground">
          בוחרות למי לשלוח, כותבות הודעה או לוקחות תבנית, ובכל מייל הפרטים האישיים (שם, משימות חסרות, שיעור הבא) מתמלאים לבד.
        </p>
      </div>

      <EmailComposer
        students={students.map((s) => ({ id: s.id, name: s.full_name, approved: s.approved, submitted: s.submitted, vars: s.vars }))}
        assignments={assignments.map((a) => ({ id: a.id, title: a.title }))}
        saved={(templates.data ?? []).map((t) => ({ id: `db:${t.id}`, name: t.name, subject: t.subject, body: t.body }))}
        preselected={(to ?? '').split(',').filter(Boolean)}
        initialTemplate={template}
        smtpReady={smtpConfigured}
        templatesReady={!templates.error}
      />

      <section aria-labelledby="log-h" className="space-y-2">
        <h2 id="log-h" className="text-lg font-semibold">
          נשלחו לאחרונה
        </h2>
        {log.error ? (
          <p className="text-sm text-fd-muted-foreground">היומן יופיע אחרי הרצת supabase/008-teacher-tools.sql ב-Supabase.</p>
        ) : log.data?.length ? (
          <ul className="divide-y rounded-xl border text-sm">
            {log.data.map((m) => (
              <li key={m.id} className="flex flex-wrap items-center justify-between gap-2 p-3">
                <span>
                  <span className="font-medium">{(m.student_id && nameOf.get(m.student_id)) || 'תלמידה שנמחקה'}</span> · {m.subject}
                </span>
                <span className={m.status === 'failed' ? 'text-red-600' : 'text-fd-muted-foreground'}>
                  {m.status === 'failed' ? 'נכשל · ' : ''}
                  {dateFmt.format(new Date(m.sent_at))}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-fd-muted-foreground">עוד לא נשלחו מיילים מהאתר.</p>
        )}
      </section>
    </main>
  );
}
