'use client';

import { useState } from 'react';
import { createClient } from '@/lib/supabase/client';

type Status = 'present' | 'late' | 'absent' | 'excused';

const options: { value: Status; label: string; active: string }[] = [
  { value: 'present', label: 'נוכחת', active: 'bg-green-600 text-white border-green-600' },
  { value: 'late', label: 'איחור', active: 'bg-amber-500 text-white border-amber-500' },
  { value: 'absent', label: 'חסרה', active: 'bg-red-600 text-white border-red-600' },
  { value: 'excused', label: 'מוצדק', active: 'bg-slate-500 text-white border-slate-500' },
];

interface Student {
  id: string;
  full_name: string;
}

export function AttendanceSheet({
  lessonId,
  students,
  initial,
}: {
  lessonId: number;
  students: Student[];
  initial: Record<string, Status>;
}) {
  const [marks, setMarks] = useState<Record<string, Status>>(initial);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(0);

  async function save(rows: { student_id: string; status: Status }[]) {
    const before = marks;
    setMarks((m) => ({ ...m, ...Object.fromEntries(rows.map((r) => [r.student_id, r.status])) }));
    setError('');
    setSaving((n) => n + 1);
    const { error } = await createClient()
      .from('attendance')
      .upsert(rows.map((r) => ({ lesson_id: lessonId, ...r })), { onConflict: 'lesson_id,student_id' });
    setSaving((n) => n - 1);
    if (error) {
      setMarks(before);
      setError('השמירה נכשלה. בדקי שהשיעור קיים בטבלת השיעורים ונסי שוב.');
    }
  }

  const unset = students.filter((s) => !marks[s.id]);
  const count = (st: Status) => students.filter((s) => marks[s.id] === st).length;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-fd-muted-foreground">
          נוכחות {count('present') + count('late')} · חסרות {count('absent')} · מוצדק {count('excused')} · לא סומנו {unset.length}
          {saving > 0 && ' · שומר...'}
        </p>
        {unset.length > 0 && (
          <button
            onClick={() => save(unset.map((s) => ({ student_id: s.id, status: 'present' })))}
            className="rounded-lg border px-3 py-1.5 text-sm font-medium hover:bg-fd-accent"
          >
            סימון כל הלא-מסומנות כנוכחות
          </button>
        )}
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <ul className="divide-y rounded-xl border">
        {students.map((s) => (
          <li key={s.id} className="flex flex-wrap items-center justify-between gap-2 p-3">
            <span className="font-medium">{s.full_name || 'ללא שם'}</span>
            <div className="flex gap-1.5">
              {options.map((o) => (
                <button
                  key={o.value}
                  onClick={() => marks[s.id] !== o.value && save([{ student_id: s.id, status: o.value }])}
                  className={`rounded-lg border px-3 py-1 text-sm ${marks[s.id] === o.value ? o.active : 'hover:bg-fd-accent'}`}
                >
                  {o.label}
                </button>
              ))}
            </div>
          </li>
        ))}
        {!students.length && <li className="p-3 text-fd-muted-foreground">אין עדיין תלמידות מאושרות.</li>}
      </ul>
    </div>
  );
}
