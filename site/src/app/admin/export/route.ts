import { NextRequest, NextResponse } from 'next/server';
import { createClient, supabaseConfigured } from '@/lib/supabase/server';
import { toCsv } from '@/lib/csv';
import { attendancePercent, defaultWeights, finalGrade, type Weights } from '@/lib/grades';

const statusHe = { present: 'נוכחת', late: 'איחור', absent: 'חסרה', excused: 'מוצדק' } as const;

/** /admin/export?type=grades|attendance — teacher only (RLS and the explicit role check). */
export async function GET(req: NextRequest) {
  if (!supabaseConfigured) return new NextResponse('Not configured', { status: 503 });
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return new NextResponse('Unauthorized', { status: 401 });
  const { data: me } = await supabase.from('profiles').select('role').eq('id', user.id).single();
  if (me?.role !== 'teacher') return new NextResponse('Forbidden', { status: 403 });

  const type = req.nextUrl.searchParams.get('type');
  const [{ data: students }, { data: lessons }, { data: assignments }, { data: subs }, { data: att }, { data: w }, { data: exams }] =
    await Promise.all([
      supabase.from('profiles').select('id, full_name').eq('role', 'student').order('full_name'),
      supabase.from('lessons').select('id').order('id'),
      supabase.from('assignments').select('id, kind, title').order('id'),
      supabase.from('submissions').select('student_id, assignment_id, grade'),
      supabase.from('attendance').select('student_id, lesson_id, status'),
      supabase.from('grade_weights').select('category, weight'),
      supabase.from('exam_grades').select('student_id, grade'),
    ]);

  let rows: (string | number | null)[][];
  if (type === 'attendance') {
    rows = [
      ['תלמידה', ...(lessons ?? []).map((l) => `שיעור ${l.id}`), 'נוכחות %'],
      ...(students ?? []).map((s) => {
        const mine = (att ?? []).filter((a) => a.student_id === s.id);
        const pct = attendancePercent(mine);
        return [
          s.full_name,
          ...(lessons ?? []).map((l) => {
            const st = mine.find((a) => a.lesson_id === l.id)?.status;
            return st ? statusHe[st as keyof typeof statusHe] : '';
          }),
          pct === null ? '' : Math.round(pct),
        ];
      }),
    ];
  } else if (type === 'grades') {
    const weights = {
      ...defaultWeights,
      ...Object.fromEntries((w ?? []).map((r) => [r.category, Number(r.weight)])),
    } as Weights;
    rows = [
      ['תלמידה', ...(assignments ?? []).map((a) => a.title), 'ציון מבחן', 'ציון משוער', 'נוכחות %'],
      ...(students ?? []).map((s) => {
        const mine = (subs ?? []).filter((x) => x.student_id === s.id);
        const exam = (exams ?? []).find((x) => x.student_id === s.id)?.grade;
        const examN = exam === undefined ? null : Number(exam);
        const final = finalGrade(assignments ?? [], mine, weights, examN);
        const pct = attendancePercent((att ?? []).filter((a) => a.student_id === s.id));
        return [
          s.full_name,
          ...(assignments ?? []).map((a) => {
            const g = mine.find((x) => x.assignment_id === a.id)?.grade;
            return g === null || g === undefined ? '' : Number(g);
          }),
          examN,
          final === null ? '' : Number(final.toFixed(1)),
          pct === null ? '' : Math.round(pct),
        ];
      }),
    ];
  } else {
    return new NextResponse('Unknown export type', { status: 400 });
  }

  return new NextResponse(toCsv(rows), {
    headers: {
      'Content-Type': 'text/csv; charset=utf-8',
      'Content-Disposition': `attachment; filename="${type}.csv"`,
      'Cache-Control': 'no-store',
    },
  });
}
