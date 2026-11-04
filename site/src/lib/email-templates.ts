import { hebrewDate } from './dates';
import { daysBetween } from './reminders';

/** Placeholders the teacher can put in a subject or body. Each is filled per student when sending. */
export const TEMPLATE_VARS = [
  { key: 'שם', label: 'שם התלמידה', sample: 'דנה' },
  { key: 'שיעור_הבא', label: 'שם השיעור הבא', sample: 'שיעור 5 – RAG' },
  { key: 'תאריך_שיעור_הבא', label: 'תאריך השיעור הבא', sample: 'יום שלישי, 10 בנובמבר' },
  { key: 'משימות_חסרות', label: 'משימות שעוד לא הוגשו', sample: '- שיעורי בית 3\n- פרויקט 1' },
  { key: 'קישור', label: 'קישור לאזור האישי', sample: 'https://…/dashboard' },
] as const;

export type Vars = Record<string, string>;

const TOKEN = /\{\{\s*([^{}]+?)\s*\}\}/g;

/** Fills {{placeholders}}. An unknown placeholder is left as written so a typo is visible in the preview. */
export function renderTemplate(text: string, vars: Vars) {
  return text.replace(TOKEN, (whole, key: string) => (key in vars ? vars[key] : whole));
}

/** Placeholders in the text that are not one of the known variables. */
export function unknownPlaceholders(text: string) {
  const known = new Set<string>(TEMPLATE_VARS.map((v) => v.key));
  return [...new Set([...text.matchAll(TOKEN)].map((m) => m[1]).filter((k) => !known.has(k)))];
}

export interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  body: string;
  builtin?: boolean;
}

export const BUILTIN_TEMPLATES: EmailTemplate[] = [
  {
    id: 'builtin:missing',
    name: 'תזכורת: משימות שלא הוגשו',
    subject: 'תזכורת: משימות שעוד לא הוגשו',
    body:
      'היי {{שם}},\n\nעדיין לא הוגשו המשימות הבאות:\n{{משימות_חסרות}}\n\n' +
      'השיעור הבא: {{שיעור_הבא}} ({{תאריך_שיעור_הבא}}).\nאפשר להגיש כאן: {{קישור}}\n\nבהצלחה!',
    builtin: true,
  },
  {
    id: 'builtin:lesson',
    name: 'הודעה על השיעור הבא',
    subject: 'השיעור הבא: {{שיעור_הבא}}',
    body: 'היי {{שם}},\n\nהשיעור הבא, "{{שיעור_הבא}}", יתקיים ב{{תאריך_שיעור_הבא}}.\n\nנתראה!',
    builtin: true,
  },
  {
    id: 'builtin:encourage',
    name: 'עידוד והמשך עבודה',
    subject: 'כל הכבוד על ההתקדמות',
    body: 'היי {{שם}},\n\nראיתי את ההתקדמות שלך בקורס, ורציתי להגיד כל הכבוד. כדאי להמשיך באותו קצב.\n\nאם משהו תקוע, אפשר לכתוב לי.',
    builtin: true,
  },
  {
    id: 'builtin:blank',
    name: 'הודעה חופשית',
    subject: '',
    body: 'היי {{שם}},\n\n',
    builtin: true,
  },
];

export interface LessonLite {
  id: number;
  title: string;
  held_on: string | null;
}
export interface AssignmentLite {
  id: number;
  lesson_id: number | null;
  title: string;
  due_at: string | null;
}

/** Assignments the student has not submitted although their date has passed (due date, or the lesson was held). */
export function missingAssignments(o: {
  today: string;
  now: Date;
  lessons: LessonLite[];
  assignments: AssignmentLite[];
  submitted: Set<number>;
}) {
  const lessonDate = new Map(o.lessons.map((l) => [l.id, l.held_on]));
  return o.assignments.filter((a) => {
    if (o.submitted.has(a.id)) return false;
    if (a.due_at && Date.parse(a.due_at) < o.now.getTime()) return true;
    const held = a.lesson_id ? lessonDate.get(a.lesson_id) : null;
    return Boolean(held && daysBetween(o.today, held) <= 0);
  });
}

export function nextLesson(lessons: LessonLite[], today: string) {
  return lessons
    .filter((l) => l.held_on && daysBetween(today, l.held_on) >= 0)
    .sort((a, b) => a.held_on!.localeCompare(b.held_on!))[0];
}

/** The placeholder values for one student. */
export function studentVars(o: {
  name: string;
  today: string;
  now: Date;
  lessons: LessonLite[];
  assignments: AssignmentLite[];
  submitted: Set<number>;
  link: string;
}): Vars {
  const next = nextLesson(o.lessons, o.today);
  const missing = missingAssignments(o);
  return {
    שם: o.name.trim() || 'תלמידה',
    שיעור_הבא: next ? `שיעור ${next.id} – ${next.title}` : 'עוד לא נקבע',
    תאריך_שיעור_הבא: next?.held_on ? hebrewDate(next.held_on) : 'עוד לא נקבע',
    משימות_חסרות: missing.length ? missing.map((a) => `- ${a.title}`).join('\n') : 'אין, הכול הוגש',
    קישור: o.link,
  };
}
