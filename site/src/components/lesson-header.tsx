import Link from 'next/link';
import { BookOpen, ClipboardList, Code2, FileText, Presentation } from 'lucide-react';

const divisionNames: Record<number, string> = { 1: 'חטיבה 1', 2: 'חטיבה 2', 3: 'חטיבה 3' };

interface Props {
  kind?: 'lesson' | 'homework' | 'project';
  lesson?: string;
  division?: number;
  schedule?: string[];
  demo?: string;
  hasHomework?: boolean;
  github?: string;
}

const btn =
  'inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium hover:bg-fd-accent transition-colors';

export function LessonHeader({ kind, lesson, division, schedule, demo, hasHomework, github }: Props) {
  if (kind === 'homework' && lesson) {
    return (
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <span className="rounded-full bg-fd-primary/10 text-fd-primary px-3 py-1 text-sm font-semibold">
          שיעורי בית · שיעור {lesson}
        </span>
        <Link href={`/docs/lessons/lesson-${lesson}`} className={btn}>
          <BookOpen className="size-4" /> חזרה לשיעור
        </Link>
        {github && (
          <a href={github} target="_blank" rel="noreferrer" className={btn}>
            <FileText className="size-4" /> שיעורי הבית ב-GitHub
          </a>
        )}
      </div>
    );
  }
  if (kind !== 'lesson' || !lesson) return null;
  return (
    <div className="mb-6 space-y-4">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="rounded-full bg-fd-primary/10 text-fd-primary px-3 py-1 font-semibold">שיעור {lesson}</span>
        {division && <span className="text-fd-muted-foreground">{divisionNames[division]}</span>}
      </div>
      {schedule && schedule.length > 0 && (
        <ol className="flex flex-wrap gap-2 text-sm">
          {schedule.map((s, i) => (
            <li key={i} className="rounded-lg border bg-fd-card px-2.5 py-1">
              {s}
            </li>
          ))}
        </ol>
      )}
      <div className="flex flex-wrap gap-2">
        {hasHomework && (
          <Link href={`/docs/lessons/lesson-${lesson}/homework`} className={btn}>
            <ClipboardList className="size-4" /> שיעורי בית
          </Link>
        )}
        {demo && (
          <a href={demo} target="_blank" rel="noreferrer" className={btn}>
            <Code2 className="size-4" /> קוד הדמו ב-GitHub
          </a>
        )}
        {github && (
          <a href={github} target="_blank" rel="noreferrer" className={btn}>
            <FileText className="size-4" /> השיעור ב-GitHub
          </a>
        )}
        {lesson === '01' && (
          <a href="/slides/01.html" target="_blank" className={btn}>
            <Presentation className="size-4" /> שקפים
          </a>
        )}
      </div>
    </div>
  );
}
