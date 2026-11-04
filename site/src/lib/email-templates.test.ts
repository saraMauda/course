import { describe, expect, it } from 'vitest';
import { renderTemplate, unknownPlaceholders, missingAssignments, nextLesson, studentVars, TEMPLATE_VARS } from './email-templates';
import { weeklyDates, addDays } from './dates';

const lessons = [
  { id: 1, title: 'פתיחה', held_on: '2026-11-03' },
  { id: 2, title: 'Prompting', held_on: '2026-11-10' },
  { id: 3, title: 'RAG', held_on: null },
];
const assignments = [
  { id: 1, lesson_id: 1, title: 'שיעורי בית 1', due_at: null },
  { id: 2, lesson_id: 2, title: 'שיעורי בית 2', due_at: null },
  { id: 3, lesson_id: 3, title: 'שיעורי בית 3', due_at: '2026-11-01T00:00:00Z' },
];
const now = new Date('2026-11-05T09:00:00Z');

describe('renderTemplate', () => {
  it('fills known placeholders, tolerating spaces, and leaves unknown ones visible', () => {
    expect(renderTemplate('היי {{שם}} / {{ שם }} / {{טעות}}', { שם: 'דנה' })).toBe('היי דנה / דנה / {{טעות}}');
  });
  it('lists unknown placeholders once', () => {
    expect(unknownPlaceholders('{{שם}} {{x}} {{x}} {{y}}')).toEqual(['x', 'y']);
  });
  it('documents every variable it can fill', () => {
    const vars = studentVars({ name: 'דנה', today: '2026-11-05', now, lessons, assignments, submitted: new Set(), link: 'L' });
    expect(Object.keys(vars).sort()).toEqual(TEMPLATE_VARS.map((v) => v.key).sort());
  });
});

describe('studentVars', () => {
  it('finds the next dated lesson on or after today', () => {
    expect(nextLesson(lessons, '2026-11-05')?.id).toBe(2);
    expect(nextLesson(lessons, '2026-11-10')?.id).toBe(2);
    expect(nextLesson(lessons, '2026-11-11')).toBeUndefined();
  });
  it('counts as missing only what is past due or whose lesson was already held', () => {
    const miss = (submitted: number[]) =>
      missingAssignments({ today: '2026-11-05', now, lessons, assignments, submitted: new Set(submitted) }).map((a) => a.id);
    expect(miss([])).toEqual([1, 3]); // 2: lesson not held yet, no due date
    expect(miss([1])).toEqual([3]);
    expect(miss([1, 3])).toEqual([]);
  });
  it('falls back gracefully with no name, no next lesson and nothing missing', () => {
    const v = studentVars({ name: ' ', today: '2026-12-01', now, lessons, assignments, submitted: new Set([1, 2, 3]), link: 'L' });
    expect(v.שם).toBe('תלמידה');
    expect(v.שיעור_הבא).toBe('עוד לא נקבע');
    expect(v.משימות_חסרות).toBe('אין, הכול הוגש');
  });
});

describe('weeklyDates', () => {
  it('steps a week at a time, across month ends', () => {
    expect(weeklyDates('2026-11-24', 3)).toEqual(['2026-11-24', '2026-12-01', '2026-12-08']);
    expect(addDays('2026-12-31', 1)).toBe('2027-01-01');
  });
});
