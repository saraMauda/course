'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { ApproveButton } from '@/components/approve-button';
import { ExamGradeInput } from '@/components/exam-grade-input';

export interface StudentRow {
  id: string;
  full_name: string;
  approved: boolean;
  exam: number | null;
  submitted: number;
  pending: number;
  att: number | null;
  final: number | null;
}

type Filter = 'all' | 'awaiting' | 'pending' | 'none';
type Sort = 'name' | 'final' | 'pending' | 'att';

const FILTERS: { value: Filter; label: string }[] = [
  { value: 'all', label: 'כולן' },
  { value: 'awaiting', label: 'ממתינות לאישור' },
  { value: 'pending', label: 'יש הגשות לבדיקה' },
  { value: 'none', label: 'לא הגישו כלום' },
];
const SORTS: { value: Sort; label: string }[] = [
  { value: 'name', label: 'שם' },
  { value: 'final', label: 'ציון משוער (נמוך ראשון)' },
  { value: 'pending', label: 'הכי הרבה לבדיקה' },
  { value: 'att', label: 'נוכחות (נמוכה ראשונה)' },
];

const num = (v: number | null, fallback: number) => (v === null ? fallback : v);

export function StudentsTable({ rows, totalAssignments }: { rows: StudentRow[]; totalAssignments: number }) {
  const [q, setQ] = useState('');
  const [filter, setFilter] = useState<Filter>('all');
  const [sort, setSort] = useState<Sort>('name');
  const [picked, setPicked] = useState<Set<string>>(new Set());

  const shown = useMemo(() => {
    const list = rows.filter((r) => {
      if (q.trim() && !r.full_name.toLowerCase().includes(q.trim().toLowerCase())) return false;
      if (filter === 'awaiting') return !r.approved;
      if (filter === 'pending') return r.pending > 0;
      if (filter === 'none') return r.submitted === 0;
      return true;
    });
    const by: Record<Sort, (a: StudentRow, b: StudentRow) => number> = {
      name: (a, b) => a.full_name.localeCompare(b.full_name, 'he'),
      final: (a, b) => num(a.final, 101) - num(b.final, 101),
      pending: (a, b) => b.pending - a.pending,
      att: (a, b) => num(a.att, 101) - num(b.att, 101),
    };
    return [...list].sort(by[sort]);
  }, [rows, q, filter, sort]);

  const shownIds = shown.map((r) => r.id);
  const allShownPicked = shownIds.length > 0 && shownIds.every((id) => picked.has(id));
  const toggle = (id: string) =>
    setPicked((p) => {
      const n = new Set(p);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  const toggleAll = () =>
    setPicked((p) => {
      const n = new Set(p);
      shownIds.forEach((id) => (allShownPicked ? n.delete(id) : n.add(id)));
      return n;
    });

  const control = 'rounded-lg border bg-fd-background px-3 py-1.5 text-sm';
  return (
    <section className="space-y-3" aria-label="תלמידות">
      <div className="flex flex-wrap items-center gap-2">
        <input
          type="search"
          className={`${control} w-48`}
          placeholder="חיפוש לפי שם"
          aria-label="חיפוש לפי שם"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select className={control} aria-label="סינון" value={filter} onChange={(e) => setFilter(e.target.value as Filter)}>
          {FILTERS.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>
        <select className={control} aria-label="מיון" value={sort} onChange={(e) => setSort(e.target.value as Sort)}>
          {SORTS.map((s) => (
            <option key={s.value} value={s.value}>
              מיון: {s.label}
            </option>
          ))}
        </select>
        <div className="ms-auto flex flex-wrap items-center gap-2">
          <span className="text-sm text-fd-muted-foreground">
            {shown.length} מוצגות{picked.size > 0 && ` · ${picked.size} נבחרו`}
          </span>
          {picked.size > 0 ? (
            <Link
              href={`/admin/email?to=${[...picked].join(',')}`}
              className="rounded-lg bg-fd-primary px-3 py-1.5 text-sm font-medium text-fd-primary-foreground"
            >
              שליחת מייל לנבחרות ({picked.size})
            </Link>
          ) : (
            <span className="text-xs text-fd-muted-foreground">סמני תלמידות כדי לשלוח להן מייל</span>
          )}
          <a href="/admin/export?type=grades" download className={`${control} font-medium hover:bg-fd-accent`}>
            ייצוא ציונים
          </a>
          <a href="/admin/export?type=attendance" download className={`${control} font-medium hover:bg-fd-accent`}>
            ייצוא נוכחות
          </a>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border">
        <table className="w-full text-start">
          <thead className="bg-fd-muted">
            <tr>
              <th scope="col" className="w-10 p-3">
                <input type="checkbox" aria-label="בחירת כל המוצגות" checked={allShownPicked} onChange={toggleAll} />
              </th>
              {['תלמידה', 'הגשות', 'לבדיקה', 'נוכחות', 'ציון מבחן', 'ציון משוער', 'גישה'].map((h) => (
                <th key={h} scope="col" className="p-3 text-start font-medium">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y">
            {shown.map((r) => (
              <tr key={r.id} className={picked.has(r.id) ? 'bg-fd-primary/5' : undefined}>
                <td className="p-3">
                  <input type="checkbox" aria-label={`בחירת ${r.full_name || 'ללא שם'}`} checked={picked.has(r.id)} onChange={() => toggle(r.id)} />
                </td>
                <td className="p-3">
                  <Link href={`/admin/students/${r.id}`} className="font-medium hover:underline">
                    {r.full_name || 'ללא שם'}
                  </Link>
                  {!r.approved && <span className="ms-2 rounded-full bg-amber-500/15 px-2 py-0.5 text-xs text-amber-700 dark:text-amber-400">לא מאושרת</span>}
                </td>
                <td className="p-3">
                  {r.submitted}/{totalAssignments}
                </td>
                <td className="p-3">
                  {r.pending > 0 ? (
                    <Link href="/admin/submissions" className="rounded-full bg-amber-500 px-2 py-0.5 text-xs font-medium text-white">
                      {r.pending}
                    </Link>
                  ) : (
                    '0'
                  )}
                </td>
                <td className={`p-3 ${r.att !== null && r.att < 70 ? 'font-medium text-red-600' : ''}`}>{r.att === null ? '—' : `${r.att.toFixed(0)}%`}</td>
                <td className="p-3">
                  <ExamGradeInput studentId={r.id} initial={r.exam} />
                </td>
                <td className="p-3 font-semibold">{r.final === null ? '—' : r.final.toFixed(1)}</td>
                <td className="p-3">
                  <ApproveButton studentId={r.id} approved={r.approved} />
                </td>
              </tr>
            ))}
            {!shown.length && (
              <tr>
                <td colSpan={8} className="p-4 text-fd-muted-foreground">
                  {rows.length ? 'אין תלמידות שמתאימות לסינון.' : 'אין עדיין תלמידות רשומות.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
