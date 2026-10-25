export type Weights = Record<'exam' | 'homework' | 'project', number>;

export interface AssignmentRow {
  id: number;
  kind: 'homework' | 'project';
}
export interface SubmissionRow {
  assignment_id: number;
  grade: number | null;
}
export interface AttendanceRow {
  status: 'present' | 'late' | 'absent' | 'excused';
}

/** Percent of the final grade. Projects: 3 x 10%. Attendance is reported separately and is not part of the grade. */
export const defaultWeights: Weights = { exam: 55, homework: 15, project: 30 };

const avg = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null);

/** Average of a category; an assignment with no graded submission counts as 0. */
function categoryAverage(kind: AssignmentRow['kind'], assignments: AssignmentRow[], subs: SubmissionRow[]) {
  const scores = assignments
    .filter((a) => a.kind === kind)
    .map((a) => subs.find((s) => s.assignment_id === a.id)?.grade ?? 0);
  return avg(scores);
}

/** Attendance %: present/late count fully, excused lessons are ignored. */
export function attendancePercent(rows: AttendanceRow[]) {
  const counted = rows.filter((r) => r.status !== 'excused');
  if (!counted.length) return null;
  return (100 * counted.filter((r) => r.status !== 'absent').length) / counted.length;
}

export function finalGrade(
  assignments: AssignmentRow[],
  subs: SubmissionRow[],
  weights: Weights = defaultWeights,
  exam: number | null = null,
) {
  // a part that has no data yet (e.g. exam not graded) is left out and the rest are re-weighted
  const parts: [number | null, number][] = [
    [exam, weights.exam],
    [categoryAverage('homework', assignments, subs), weights.homework],
    [categoryAverage('project', assignments, subs), weights.project],
  ];
  const used = parts.filter((p): p is [number, number] => p[0] !== null);
  const totalWeight = used.reduce((a, [, w]) => a + w, 0);
  if (!totalWeight) return null;
  return used.reduce((a, [v, w]) => a + v * w, 0) / totalWeight;
}
