import { describe, expect, it } from 'vitest';
import { attendancePercent, defaultWeights, finalGrade, type AssignmentRow, type SubmissionRow } from './grades';

const hw = (id: number): AssignmentRow => ({ id, kind: 'homework' });
const pr = (id: number): AssignmentRow => ({ id, kind: 'project' });
const sub = (assignment_id: number, grade: number | null): SubmissionRow => ({ assignment_id, grade });

describe('attendancePercent', () => {
  it('returns null with no rows', () => expect(attendancePercent([])).toBeNull());
  it('counts present and late fully, absent as zero', () => {
    expect(attendancePercent([{ status: 'present' }, { status: 'late' }, { status: 'absent' }, { status: 'absent' }])).toBe(50);
  });
  it('ignores excused lessons', () => {
    expect(attendancePercent([{ status: 'present' }, { status: 'excused' }])).toBe(100);
    expect(attendancePercent([{ status: 'excused' }])).toBeNull();
  });
});

describe('finalGrade', () => {
  it('is null when there is nothing to grade', () => expect(finalGrade([], [], defaultWeights, null)).toBeNull());

  it('combines exam, homework and projects by weight', () => {
    const assignments = [hw(1), hw(2), pr(101)];
    const subs = [sub(1, 100), sub(2, 80), sub(101, 60)];
    // exam 90*55 + hw avg 90*15 + project 60*30 = 4950 + 1350 + 1800 = 8100 / 100
    expect(finalGrade(assignments, subs, defaultWeights, 90)).toBeCloseTo(81);
  });

  it('counts a missing submission as zero', () => {
    expect(finalGrade([hw(1), hw(2)], [sub(1, 100)], { exam: 0, homework: 100, project: 0 })).toBe(50);
  });

  it('counts a submitted but ungraded work as zero too', () => {
    expect(finalGrade([hw(1)], [sub(1, null)], { exam: 0, homework: 100, project: 0 })).toBe(0);
  });

  it('re-weights when the exam has no grade yet', () => {
    const assignments = [hw(1), pr(101)];
    const subs = [sub(1, 100), sub(101, 50)];
    // (100*15 + 50*30) / 45
    expect(finalGrade(assignments, subs, defaultWeights, null)).toBeCloseTo(66.667, 2);
  });

  it('uses only the exam when there are no assignments', () => {
    expect(finalGrade([], [], defaultWeights, 77)).toBe(77);
  });
});
