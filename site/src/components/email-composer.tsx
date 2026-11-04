'use client';

import { useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import {
  BUILTIN_TEMPLATES,
  TEMPLATE_VARS,
  renderTemplate,
  unknownPlaceholders,
  type EmailTemplate,
  type Vars,
} from '@/lib/email-templates';

export interface ComposerStudent {
  id: string;
  name: string;
  approved: boolean;
  submitted: number[];
  vars: Vars;
}

type Result = { sent: number; failed: { name: string; reason: string }[] } | { error: string };

const control = 'rounded-lg border bg-fd-background px-3 py-1.5 text-sm';
const smallBtn = 'rounded-lg border px-3 py-1.5 text-sm font-medium hover:bg-fd-accent disabled:opacity-50';

export function EmailComposer({
  students,
  assignments,
  saved,
  preselected,
  initialTemplate,
  smtpReady,
  templatesReady,
}: {
  students: ComposerStudent[];
  assignments: { id: number; title: string }[];
  saved: EmailTemplate[];
  preselected: string[];
  initialTemplate?: string;
  smtpReady: boolean;
  templatesReady: boolean;
}) {
  const router = useRouter();
  const [templates, setTemplates] = useState<EmailTemplate[]>(saved);
  const all = useMemo(() => [...BUILTIN_TEMPLATES, ...templates], [templates]);
  const first = all.find((t) => t.id === initialTemplate) ?? BUILTIN_TEMPLATES[BUILTIN_TEMPLATES.length - 1];

  const [templateId, setTemplateId] = useState(first.id);
  const [subject, setSubject] = useState(first.subject);
  const [body, setBody] = useState(first.body);
  const [picked, setPicked] = useState<Set<string>>(new Set(preselected.filter((id) => students.some((s) => s.id === id))));
  const [q, setQ] = useState('');
  const [missingFor, setMissingFor] = useState<number>(assignments[0]?.id ?? 0);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [note, setNote] = useState('');

  const subjectRef = useRef<HTMLInputElement>(null);
  const bodyRef = useRef<HTMLTextAreaElement>(null);
  const lastField = useRef<'subject' | 'body'>('body');

  const current = all.find((t) => t.id === templateId);
  const shown = students.filter((s) => !q.trim() || s.name.toLowerCase().includes(q.trim().toLowerCase()));
  const chosen = students.filter((s) => picked.has(s.id));
  const sample = chosen[0];
  const sampleVars = sample?.vars ?? Object.fromEntries(TEMPLATE_VARS.map((v) => [v.key, v.sample]));
  const unknown = unknownPlaceholders(subject + '\n' + body);
  const canSend = smtpReady && chosen.length > 0 && subject.trim() && body.trim() && unknown.length === 0 && !busy;

  const toggle = (id: string) =>
    setPicked((p) => {
      const n = new Set(p);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });

  function pickTemplate(id: string) {
    const t = all.find((x) => x.id === id);
    if (!t) return;
    setTemplateId(id);
    setSubject(t.subject);
    setBody(t.body);
    setNote('');
  }

  function insertVar(key: string) {
    const token = `{{${key}}}`;
    const field = lastField.current === 'subject' ? subjectRef.current : bodyRef.current;
    const setter = lastField.current === 'subject' ? setSubject : setBody;
    const value = lastField.current === 'subject' ? subject : body;
    const at = field?.selectionStart ?? value.length;
    const end = field?.selectionEnd ?? at;
    setter(value.slice(0, at) + token + value.slice(end));
    requestAnimationFrame(() => {
      field?.focus();
      field?.setSelectionRange(at + token.length, at + token.length);
    });
  }

  async function saveNew() {
    const name = window.prompt('איך לקרוא לתבנית?')?.trim();
    if (!name) return;
    const { data, error } = await createClient().from('email_templates').insert({ name, subject, body }).select('id, name, subject, body').single();
    if (error || !data) return setNote('שמירת התבנית נכשלה');
    const t: EmailTemplate = { id: `db:${data.id}`, name: data.name, subject: data.subject, body: data.body };
    setTemplates((list) => [t, ...list]);
    setTemplateId(t.id);
    setNote(`התבנית "${name}" נשמרה`);
  }

  async function updateCurrent() {
    if (!current || current.builtin) return;
    const { error } = await createClient().from('email_templates').update({ subject, body }).eq('id', Number(current.id.slice(3)));
    if (error) return setNote('העדכון נכשל');
    setTemplates((list) => list.map((t) => (t.id === current.id ? { ...t, subject, body } : t)));
    setNote(`התבנית "${current.name}" עודכנה`);
  }

  async function removeCurrent() {
    if (!current || current.builtin || !window.confirm(`למחוק את התבנית "${current.name}"?`)) return;
    const { error } = await createClient().from('email_templates').delete().eq('id', Number(current.id.slice(3)));
    if (error) return setNote('המחיקה נכשלה');
    setTemplates((list) => list.filter((t) => t.id !== current.id));
    pickTemplate(BUILTIN_TEMPLATES[BUILTIN_TEMPLATES.length - 1].id);
    setNote('התבנית נמחקה');
  }

  async function send() {
    if (!window.confirm(`לשלוח מייל ל-${chosen.length} תלמידות?`)) return;
    setBusy(true);
    setResult(null);
    try {
      const res = await fetch('/api/email/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: chosen.map((s) => s.id), subject, body }),
      });
      const data = await res.json().catch(() => ({}));
      setResult(res.ok ? data : { error: res.status === 503 ? 'שליחת מיילים לא הוגדרה בשרת (SMTP)' : 'השליחה נכשלה' });
      if (res.ok) router.refresh();
    } catch {
      setResult({ error: 'השליחה נכשלה' });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
      <section className="space-y-3 rounded-xl border p-4" aria-label="למי לשלוח">
        <h2 className="font-semibold">למי לשלוח ({chosen.length} נבחרו)</h2>
        <input type="search" className={`${control} w-full`} placeholder="חיפוש לפי שם" aria-label="חיפוש תלמידה" value={q} onChange={(e) => setQ(e.target.value)} />
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <button type="button" className={smallBtn} onClick={() => setPicked(new Set(students.filter((s) => s.approved).map((s) => s.id)))}>
            כל המאושרות
          </button>
          <button type="button" className={smallBtn} onClick={() => setPicked(new Set())}>
            ניקוי
          </button>
        </div>
        {assignments.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <select className={control} aria-label="משימה" value={missingFor} onChange={(e) => setMissingFor(Number(e.target.value))}>
              {assignments.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.title}
                </option>
              ))}
            </select>
            <button
              type="button"
              className={smallBtn}
              onClick={() => setPicked(new Set(students.filter((s) => s.approved && !s.submitted.includes(missingFor)).map((s) => s.id)))}
            >
              מי שלא הגישה
            </button>
          </div>
        )}
        <ul className="max-h-96 divide-y overflow-y-auto rounded-lg border">
          {shown.map((s) => (
            <li key={s.id}>
              <label className="flex cursor-pointer items-center gap-2 p-2 text-sm hover:bg-fd-accent">
                <input type="checkbox" checked={picked.has(s.id)} onChange={() => toggle(s.id)} />
                <span>{s.name || 'ללא שם'}</span>
                {!s.approved && <span className="text-xs text-amber-700 dark:text-amber-400">לא מאושרת</span>}
              </label>
            </li>
          ))}
          {!shown.length && <li className="p-3 text-sm text-fd-muted-foreground">לא נמצאו תלמידות.</li>}
        </ul>
      </section>

      <section className="space-y-3 rounded-xl border p-4" aria-label="ההודעה">
        <h2 className="font-semibold">ההודעה</h2>

        <div className="flex flex-wrap items-center gap-2">
          <select className={`${control} min-w-48`} aria-label="תבנית" value={templateId} onChange={(e) => pickTemplate(e.target.value)}>
            <optgroup label="תבניות מוכנות">
              {BUILTIN_TEMPLATES.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </optgroup>
            {templates.length > 0 && (
              <optgroup label="התבניות שלי">
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </optgroup>
            )}
          </select>
          {templatesReady && (
            <>
              <button type="button" className={smallBtn} onClick={saveNew}>
                שמירה כתבנית חדשה
              </button>
              {current && !current.builtin && (
                <>
                  <button type="button" className={smallBtn} onClick={updateCurrent}>
                    עדכון התבנית
                  </button>
                  <button type="button" className="rounded-lg px-3 py-1.5 text-sm text-red-600 hover:bg-red-500/10" onClick={removeCurrent}>
                    מחיקה
                  </button>
                </>
              )}
            </>
          )}
        </div>
        {!templatesReady && <p className="text-xs text-amber-700 dark:text-amber-400">כדי לשמור תבניות משלך צריך להריץ ב-Supabase את supabase/008-teacher-tools.sql.</p>}
        {note && (
          <p role="status" className="text-sm text-fd-muted-foreground">
            {note}
          </p>
        )}

        <input
          ref={subjectRef}
          className={`${control} w-full`}
          placeholder="נושא"
          aria-label="נושא"
          value={subject}
          onFocus={() => (lastField.current = 'subject')}
          onChange={(e) => setSubject(e.target.value)}
        />
        <textarea
          ref={bodyRef}
          className={`${control} w-full leading-6`}
          rows={10}
          placeholder="תוכן ההודעה"
          aria-label="תוכן ההודעה"
          value={body}
          onFocus={() => (lastField.current = 'body')}
          onChange={(e) => setBody(e.target.value)}
        />

        <div className="space-y-1">
          <div className="text-xs text-fd-muted-foreground">לחיצה מוסיפה את הפרט האישי במקום הסמן. בכל מייל הוא מתמלא לפי התלמידה:</div>
          <div className="flex flex-wrap gap-1.5">
            {TEMPLATE_VARS.map((v) => (
              <button key={v.key} type="button" title={v.label} onClick={() => insertVar(v.key)} className="rounded-full border px-2.5 py-0.5 text-xs hover:bg-fd-accent">
                {v.label}
              </button>
            ))}
          </div>
        </div>

        {unknown.length > 0 && (
          <p role="alert" className="text-sm text-red-600">
            פרט אישי שלא מוכר: {unknown.map((u) => `{{${u}}}`).join(', ')}. אפשר לבחור רק מהכפתורים שלמעלה.
          </p>
        )}

        <div className="space-y-1 rounded-lg border bg-fd-muted/40 p-3">
          <div className="text-xs text-fd-muted-foreground">תצוגה מקדימה · {sample ? `כך זה ייראה ל${sample.name || 'תלמידה הראשונה שנבחרה'}` : 'בדוגמה (עוד לא נבחרו תלמידות)'}</div>
          <div className="font-medium">{renderTemplate(subject, sampleVars) || '(בלי נושא)'}</div>
          <p className="whitespace-pre-wrap text-sm">{renderTemplate(body, sampleVars)}</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={send}
            disabled={!canSend}
            aria-busy={busy}
            className="rounded-lg bg-fd-primary px-5 py-2 font-medium text-fd-primary-foreground disabled:opacity-50"
          >
            {busy ? 'שולחת...' : `שליחה ל-${chosen.length} תלמידות`}
          </button>
          {!smtpReady && <span className="text-sm text-amber-700 dark:text-amber-400">שליחת מיילים עוד לא הוגדרה בשרת (משתני SMTP).</span>}
        </div>

        {result && 'error' in result && (
          <p role="alert" className="text-sm text-red-600">
            {result.error}
          </p>
        )}
        {result && 'sent' in result && (
          <div role="status" className="space-y-1 text-sm">
            <p className="text-green-600">נשלחו {result.sent} מיילים.</p>
            {result.failed.length > 0 && (
              <p className="text-red-600">לא נשלח ל: {result.failed.map((f) => `${f.name} (${f.reason})`).join(', ')}</p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
