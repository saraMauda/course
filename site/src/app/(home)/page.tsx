import Link from 'next/link';
import { ArrowLeft, FolderGit2 } from 'lucide-react';
import course from '@/lib/course.json';

const divisions = [
  { n: 1, title: 'חטיבה 1', sub: 'יסודות, Prompting, RAG', project: '/docs/projects/project-01' },
  { n: 2, title: 'חטיבה 2', sub: 'Skills, MCP, Agents, LangChain', project: '/docs/projects/project-02' },
  { n: 3, title: 'חטיבה 3', sub: 'LangGraph, HITL, LangSmith', project: '/docs/projects/project-03' },
];

export default function HomePage() {
  const first = course.lessons[0]?.slug ?? '/docs';
  return (
    <main className="flex flex-col flex-1">
      <section className="relative overflow-hidden border-b bg-gradient-to-b from-fd-primary/10 to-transparent">
        <div className="mx-auto max-w-3xl px-4 py-20 text-center">
          <p className="mb-3 text-sm font-semibold text-fd-primary">15 שיעורים · 3 פרויקטים</p>
          <h1 className="mb-4 text-4xl font-bold sm:text-5xl">Agentic AI</h1>
          <p className="text-lg text-fd-muted-foreground">
            מ-LLM ו-Prompt Engineering, דרך RAG ו-MCP, ועד סוכנים מרובי-שלבים ב-LangGraph. חומרי שיעור, קוד ושיעורי בית – הכל במקום אחד.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link href={first} className="inline-flex items-center gap-2 rounded-lg bg-fd-primary px-5 py-2.5 font-medium text-fd-primary-foreground">
              התחלת הקורס <ArrowLeft className="size-4" />
            </Link>
            <Link href="/dashboard" className="rounded-lg border bg-fd-background px-5 py-2.5 font-medium hover:bg-fd-accent">
              האזור האישי
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-5xl space-y-10 px-4 py-12">
        {divisions.map((d) => {
          const lessons = course.lessons.filter((l) => l.division === d.n);
          return (
            <div key={d.n}>
              <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
                <div>
                  <h2 className="text-2xl font-bold">{d.title}</h2>
                  <p className="text-fd-muted-foreground">{d.sub}</p>
                </div>
                <Link href={d.project} className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium hover:bg-fd-accent">
                  <FolderGit2 className="size-4" /> פרויקט {d.n}
                </Link>
              </div>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {lessons.map((l) => (
                  <Link
                    key={l.num}
                    href={l.slug}
                    className="group rounded-xl border bg-fd-card p-4 transition-colors hover:border-fd-primary/50 hover:bg-fd-accent"
                  >
                    <div className="mb-1 text-sm font-semibold text-fd-primary">שיעור {l.num}</div>
                    <div className="font-medium leading-snug">{l.title}</div>
                    {l.hasHomework && <div className="mt-2 text-xs text-fd-muted-foreground">כולל שיעורי בית</div>}
                  </Link>
                ))}
              </div>
            </div>
          );
        })}
      </section>
    </main>
  );
}
