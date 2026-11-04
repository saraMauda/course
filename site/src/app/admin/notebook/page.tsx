import Link from 'next/link';
import { requireTeacher } from '@/lib/admin';
import { NotebookView } from '@/components/notebook-view';
import { isNotebookPath, parseNotebook, STORAGE_PATH } from '@/lib/notebook';

export const metadata = { title: 'צפייה ב-notebook' };

const MAX_BYTES = 5 * 1024 * 1024;

export default async function NotebookPage({ searchParams }: { searchParams: Promise<{ path?: string }> }) {
  const { supabase } = await requireTeacher();
  const { path } = await searchParams;

  const box = (text: string) => (
    <main className="mx-auto max-w-4xl space-y-4 p-6">
      <p className="rounded-xl border p-4 text-fd-muted-foreground">{text}</p>
      <Link href="/admin/submissions" className="underline">
        חזרה להגשות
      </Link>
    </main>
  );

  if (!path || !STORAGE_PATH.test(path) || !isNotebookPath(path)) return box('הקובץ המבוקש אינו notebook תקין.');

  const [studentId, assignmentId] = path.split('/');
  const [{ data: student }, { data: assignment }, file, { data: signed }] = await Promise.all([
    supabase.from('profiles').select('full_name').eq('id', studentId).maybeSingle(),
    supabase.from('assignments').select('title').eq('id', Number(assignmentId)).maybeSingle(),
    supabase.storage.from('submissions').download(path),
    supabase.storage.from('submissions').createSignedUrl(path, 3600),
  ]);
  if (file.error || !file.data) return box('לא הצלחתי לפתוח את הקובץ (ייתכן שנמחק).');

  const download = signed?.signedUrl && (
    <a href={signed.signedUrl} download className="rounded-lg border px-3 py-1.5 text-sm font-medium hover:bg-fd-accent">
      הורדת הקובץ
    </a>
  );
  if (file.data.size > MAX_BYTES) return <main className="mx-auto max-w-4xl space-y-4 p-6">{download}<p>הקובץ גדול מדי להצגה כאן. אפשר להוריד אותו.</p></main>;

  const cells = parseNotebook(await file.data.text());
  if (!cells) return box('הקובץ אינו notebook תקין.');

  return (
    <main className="mx-auto max-w-4xl space-y-5 p-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold">{student?.full_name || 'ללא שם'}</h1>
          <p className="text-sm text-fd-muted-foreground">
            {assignment?.title ?? 'משימה'} · {cells.filter((c) => c.type === 'code').length} תאי קוד
          </p>
        </div>
        <div className="flex gap-2">
          {download}
          <Link href={`/admin/submissions?assignment=${assignmentId}`} className="rounded-lg border px-3 py-1.5 text-sm font-medium hover:bg-fd-accent">
            חזרה להגשות
          </Link>
        </div>
      </div>
      <NotebookView cells={cells} />
    </main>
  );
}
