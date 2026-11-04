import nodemailer, { type Transporter } from 'nodemailer';

export const smtpConfigured = Boolean(process.env.SMTP_HOST && process.env.SMTP_USER && process.env.SMTP_PASS);

export function escapeHtml(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export type SubmissionEvent = 'returned' | 'graded';

/** Hebrew, right-to-left notification for a student about one assignment. */
export function buildSubmissionMail(opts: {
  event: SubmissionEvent;
  studentName: string;
  assignmentTitle: string;
  grade?: number | null;
  feedback?: string | null;
  link?: string;
}) {
  const name = opts.studentName.trim() || 'שלום';
  const hello = opts.studentName.trim() ? `היי ${name},` : 'שלום,';
  const feedback = opts.feedback?.trim();

  const subject =
    opts.event === 'returned'
      ? `ההגשה "${opts.assignmentTitle}" הוחזרה לתיקון`
      : `ההגשה "${opts.assignmentTitle}" נבדקה`;
  const lines =
    opts.event === 'returned'
      ? [`ההגשה שלך במשימה "${opts.assignmentTitle}" הוחזרה לתיקון.`, 'אפשר להיכנס, לתקן ולהגיש מחדש.']
      : [`ההגשה שלך במשימה "${opts.assignmentTitle}" נבדקה.`, `ציון: ${opts.grade ?? '-'}`];
  if (feedback) lines.push('', 'משוב מהמורה:', feedback);
  if (opts.link) lines.push('', opts.link);

  const text = [hello, '', ...lines].join('\n');
  const html =
    `<div dir="rtl" style="font-family:Arial,sans-serif;line-height:1.6">` +
    `<p>${escapeHtml(hello)}</p>` +
    lines.map((l) => (l ? `<p style="margin:0 0 8px;white-space:pre-wrap">${escapeHtml(l)}</p>` : '<br>')).join('') +
    `</div>`;
  return { subject, text, html };
}

function layout(hello: string, lines: string[]) {
  const text = [hello, '', ...lines].join('\n');
  const html =
    `<div dir="rtl" style="font-family:Arial,sans-serif;line-height:1.6">` +
    `<p>${escapeHtml(hello)}</p>` +
    lines.map((l) => (l ? `<p style="margin:0 0 8px;white-space:pre-wrap">${escapeHtml(l)}</p>` : '<br>')).join('') +
    `</div>`;
  return { text, html };
}

function hebrewDate(day: string) {
  return new Date(`${day}T12:00:00Z`).toLocaleDateString('he-IL', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    timeZone: 'Asia/Jerusalem',
  });
}

/** Automatic reminders sent by the daily job. */
export function buildReminderMail(opts: {
  kind: 'homework_missing' | 'lesson_soon';
  studentName: string;
  lessonTitle: string;
  lessonDate: string; // YYYY-MM-DD
  assignmentTitle?: string;
  link?: string;
}) {
  const hello = opts.studentName.trim() ? `היי ${opts.studentName.trim()},` : 'שלום,';
  const when = hebrewDate(opts.lessonDate);
  const subject =
    opts.kind === 'homework_missing'
      ? `תזכורת: עדיין לא הוגשו ${opts.assignmentTitle}`
      : `תזכורת: מחר שיעור – ${opts.lessonTitle}`;
  const lines =
    opts.kind === 'homework_missing'
      ? [
          `עוד לא הגשת את "${opts.assignmentTitle}", והשיעור הבא ("${opts.lessonTitle}") ב${when}.`,
          'כדאי להגיש לפני השיעור.',
        ]
      : [`מחר, ${when}, מתקיים השיעור "${opts.lessonTitle}".`];
  if (opts.link) lines.push('', opts.link);
  return { subject, ...layout(hello, lines) };
}

let transport: Transporter | undefined;

export async function sendMail(to: string, mail: { subject: string; text: string; html: string }) {
  if (!smtpConfigured) throw new Error('SMTP is not configured');
  const port = Number(process.env.SMTP_PORT) || 587;
  transport ??= nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port,
    secure: port === 465,
    auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS },
  });
  await transport.sendMail({ from: process.env.SMTP_FROM || process.env.SMTP_USER, to, ...mail });
}
