export interface Lesson {
  id: number;
  title: string;
  held_on: string | null; // YYYY-MM-DD
}
export interface Assignment {
  id: number;
  lesson_id: number | null;
  kind: string;
  title: string;
}
export interface Student {
  id: string;
  full_name: string;
  email: string;
}

export type ReminderKind = 'homework_missing' | 'lesson_soon';

export interface Reminder {
  student: Student;
  kind: ReminderKind;
  refId: number; // assignment id for homework_missing, lesson id for lesson_soon
  lesson: Lesson; // the upcoming lesson
  assignment?: Assignment;
}

/** Days before a lesson that the "homework not submitted" reminder starts. */
export const HOMEWORK_REMINDER_DAYS = 2;

/** Today's date (YYYY-MM-DD) in the course's time zone. */
export function todayInIsrael(now = new Date()) {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Jerusalem' }).format(now);
}

export function daysBetween(from: string, to: string) {
  return Math.round((Date.parse(`${to}T00:00:00Z`) - Date.parse(`${from}T00:00:00Z`)) / 86_400_000);
}

/**
 * Which reminders are due today.
 *  - homework_missing: from 2 days before lesson N until the lesson, for every student who has not
 *    submitted the homework of lesson N-1.
 *  - lesson_soon: the day before a lesson, for every student.
 * The window (not an exact day) lets a skipped day catch up; `already` keeps each one to a single email.
 */
export function planReminders(opts: {
  today: string;
  lessons: Lesson[];
  assignments: Assignment[];
  students: Student[];
  submitted: Set<string>; // `${studentId}:${assignmentId}`
  already: Set<string>; // `${studentId}:${kind}:${refId}`
}): Reminder[] {
  const out: Reminder[] = [];
  const push = (r: Reminder) => {
    if (!opts.already.has(`${r.student.id}:${r.kind}:${r.refId}`)) out.push(r);
  };

  for (const lesson of opts.lessons) {
    if (!lesson.held_on) continue;
    const days = daysBetween(opts.today, lesson.held_on);

    if (days === 1) {
      for (const student of opts.students) push({ student, kind: 'lesson_soon', refId: lesson.id, lesson });
    }

    if (days >= 0 && days <= HOMEWORK_REMINDER_DAYS) {
      const homework = opts.assignments.filter((a) => a.kind === 'homework' && a.lesson_id === lesson.id - 1);
      for (const assignment of homework) {
        for (const student of opts.students) {
          if (opts.submitted.has(`${student.id}:${assignment.id}`)) continue;
          push({ student, kind: 'homework_missing', refId: assignment.id, lesson, assignment });
        }
      }
    }
  }
  return out;
}
