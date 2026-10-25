'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

export function ExamGradeInput({ studentId, initial }: { studentId: string; initial: number | null }) {
  const router = useRouter();
  const [value, setValue] = useState(initial === null ? '' : String(initial));
  const [status, setStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  async function save() {
    const trimmed = value.trim();
    const supabase = createClient();
    setStatus('saving');
    if (trimmed === '') {
      const { error } = await supabase.from('exam_grades').delete().eq('student_id', studentId);
      if (error) return setStatus('error');
    } else {
      const n = Number(trimmed);
      if (!Number.isFinite(n) || n < 0 || n > 100) return setStatus('error');
      const { error } = await supabase.from('exam_grades').upsert({ student_id: studentId, grade: n });
      if (error) return setStatus('error');
    }
    setStatus('saved');
    router.refresh();
  }

  return (
    <div className="flex items-center gap-2">
      <input
        type="number"
        min={0}
        max={100}
        step="0.5"
        dir="ltr"
        value={value}
        onChange={(e) => {
          setValue(e.target.value);
          setStatus('idle');
        }}
        onBlur={() => value !== (initial === null ? '' : String(initial)) && save()}
        onKeyDown={(e) => e.key === 'Enter' && (e.currentTarget.blur(), undefined)}
        className="w-20 rounded-lg border bg-fd-background px-2 py-1"
        aria-label="ציון מבחן"
      />
      <span className="text-xs text-fd-muted-foreground">
        {status === 'saving' && 'שומר...'}
        {status === 'saved' && 'נשמר'}
        {status === 'error' && <span className="text-red-600">שגיאה</span>}
      </span>
    </div>
  );
}
