import { describe, expect, it } from 'vitest';
import { daysBetween, planReminders, todayInIsrael, type Assignment, type Lesson, type Student } from './reminders';

const lessons: Lesson[] = [
  { id: 1, title: 'א', held_on: '2026-11-01' },
  { id: 2, title: 'ב', held_on: '2026-11-10' },
  { id: 3, title: 'ג', held_on: null },
];
const assignments: Assignment[] = [
  { id: 1, lesson_id: 1, kind: 'homework', title: 'שיעורי בית 01' },
  { id: 101, lesson_id: null, kind: 'project', title: 'פרויקט 1' },
];
const dana: Student = { id: 'd', full_name: 'דנה', email: 'd@x.com' };
const noa: Student = { id: 'n', full_name: 'נועה', email: 'n@x.com' };
const base = { lessons, assignments, students: [dana, noa], submitted: new Set<string>(), already: new Set<string>() };

describe('planReminders', () => {
  it('reminds only students missing the previous lesson homework, 2 days before', () => {
    const r = planReminders({ ...base, today: '2026-11-08', submitted: new Set(['d:1']) });
    expect(r.map((x) => [x.student.id, x.kind, x.refId])).toEqual([['n', 'homework_missing', 1]]);
  });
  it('is quiet before the window', () => {
    expect(planReminders({ ...base, today: '2026-11-07' })).toEqual([]);
  });
  it('catches up a skipped day but not after the lesson', () => {
    expect(planReminders({ ...base, today: '2026-11-09' }).filter((x) => x.kind === 'homework_missing')).toHaveLength(2);
    expect(planReminders({ ...base, today: '2026-11-11' })).toEqual([]);
  });
  it('sends a lesson-tomorrow reminder to everyone, only the day before', () => {
    const r = planReminders({ ...base, today: '2026-11-09' }).filter((x) => x.kind === 'lesson_soon');
    expect(r).toHaveLength(2);
    expect(planReminders({ ...base, today: '2026-11-08' }).some((x) => x.kind === 'lesson_soon')).toBe(false);
  });
  it('skips what was already sent and lessons without a date', () => {
    const r = planReminders({ ...base, today: '2026-11-08', already: new Set(['n:homework_missing:1', 'd:homework_missing:1']) });
    expect(r).toEqual([]);
  });
  it('date helpers', () => {
    expect(daysBetween('2026-11-08', '2026-11-10')).toBe(2);
    expect(todayInIsrael(new Date('2026-11-08T22:30:00Z'))).toBe('2026-11-09');
  });
});
