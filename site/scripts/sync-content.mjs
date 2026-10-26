// Syncs the course markdown (../lessons, ../projects, ../assets) into the site.
// Re-runnable: `npm run sync`. Teacher-only material (מערכי-מסירה) is never copied.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const siteRoot = path.resolve(here, '..');
const courseRoot = path.resolve(siteRoot, '..');
const docsOut = path.join(siteRoot, 'content', 'docs');
const publicOut = path.join(siteRoot, 'public');

// On a host that only has the site/ folder (e.g. Vercel with Root Directory = site) the course sources are
// missing; the generated content is committed, so just use it.
if (!fs.existsSync(path.join(courseRoot, 'lessons'))) {
  console.log('course sources not found next to site/, using the committed content');
  process.exit(0);
}

// Where "demos/..." links point. Override with COURSE_GITHUB_BASE env var.
const GH_BASE =
  process.env.COURSE_GITHUB_BASE ?? 'https://github.com/saraMauda/course/tree/main';

const divisionLabels = {
  1: 'חטיבה 1 · יסודות, Prompting, RAG',
  2: 'חטיבה 2 · Skills, MCP, Agents, LangChain',
  3: 'חטיבה 3 · LangGraph, HITL, LangSmith',
};
const divisionOf = (num) => (num <= 5 ? 1 : num <= 10 ? 2 : 3);

const projectSlugs = {
  'project-01-service-bot': 'project-01',
  'project-02-research-agent': 'project-02',
  'project-02-דף-הנחיה-לסטודנטים': 'project-02-guide',
  'project-03-notebooklm': 'project-03',
  'project-03-דף-הנחיה-לסטודנטים': 'project-03-guide',
};

function rewriteLinks(text) {
  return text
    .replace(/\]\(\.\.\/demos\/([^)]*)\)/g, (_, p) => `](${GH_BASE}/demos/${p})`)
    .replace(/\]\(\.\.\/assets\/(01-שקפים\.html)\)/g, '](/slides/01.html)')
    .replace(/\]\(\.\.\/assets\/([^)]+\.(?:png|svg))\)/g, (_, f) => `](/assets/${f})`)
    .replace(/\]\(\.\.\/lessons\/(\d\d)-[^)]*\.md\)/g, (_, n) => `](/docs/lessons/lesson-${n})`)
    .replace(/\]\((?:\.\.\/projects\/)?(project-0\d-[^)]*?)\.md\)/g, (m, name) =>
      projectSlugs[name] ? `](/docs/projects/${projectSlugs[name]})` : m,
    );
}

const LEADING_DECOR = /^[\p{Extended_Pictographic}️‍\s]+/u;
const cleanTitle = (t) =>
  t.replace(/^\d+\s*\|\s*/, '').replace(LEADING_DECOR, '').replace(/^פרויקט (\d)\s*\|\s*/, 'פרויקט $1 · ').trim();

function split(text) {
  const lines = text.replace(/^﻿/, '').split(/\r?\n/);
  const i = lines.findIndex((l) => l.startsWith('# '));
  const rawTitle = i >= 0 ? lines[i].slice(2).trim() : 'ללא כותרת';
  if (i >= 0) lines.splice(i, 1);
  return { rawTitle, body: lines.join('\n').trim() + '\n' };
}

/** Pulls the "מבנה מפגש / חטיבה / דמו" quote block into structured fields and removes it from the body. */
function extractLessonMeta(body) {
  const m = body.match(/^(\s*(?:>.*\r?\n)+)/);
  if (!m || !m[1].includes('מבנה מפגש')) return { body, meta: {} };
  const quote = m[1];
  const strip = (s) => s.replace(/\*\*/g, '').replace(/\[([^\]]*)\]\([^)]*\)/g, '$1').replace(/`/g, '').trim();
  const meta = {};
  for (const raw of quote.split(/\r?\n/)) {
    const line = raw.replace(/^>\s?/, '').trim();
    if (line.includes('מבנה מפגש:')) {
      meta.schedule = strip(line.split('מבנה מפגש:')[1]).split(' · ').map((s) => s.trim()).filter(Boolean);
    } else if (/^\*\*חטיבה \d/.test(line)) {
      const parts = strip(line).split(' · ');
      meta.division = Number(parts[0].match(/\d/)[0]);
      meta.note = parts.slice(1).join(' · ');
    } else if (line.includes('דמו:')) {
      const d = line.match(/\]\(\.\.\/(demos\/[^)]*)\)/);
      if (d) meta.demo = d[1];
    }
  }
  return { body: body.slice(quote.length).replace(/^\s*---\s*\n/, '').trimStart(), meta };
}

// Files with ```mermaid fences become .mdx so the diagram can render as a component.
const MERMAID_RE = /```mermaid\r?\n([\s\S]*?)```/g;

function write(file, fields, body) {
  if (MERMAID_RE.test(body)) {
    body = body.replace(MERMAID_RE, (_, code) => `<Mermaid chart={${JSON.stringify(code.trim())}} />`);
    file = file.replace(/\.md$/, '.mdx');
  }
  MERMAID_RE.lastIndex = 0;
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const fm = Object.entries(fields)
    .filter(([, v]) => v !== undefined && v !== '')
    .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
    .join('\n');
  fs.writeFileSync(file, `---\n${fm}\n---\n\n${rewriteLinks(body)}`);
}

// clean previous generated content
fs.rmSync(path.join(docsOut, 'lessons'), { recursive: true, force: true });
fs.rmSync(path.join(docsOut, 'projects'), { recursive: true, force: true });

const courseData = { lessons: [], projects: [] };

// lessons
const lessonsDir = path.join(courseRoot, 'lessons');
const homeworkBodies = {};
for (const f of fs.readdirSync(lessonsDir).filter((f) => f.endsWith('.md'))) {
  const m = f.match(/^(\d\d)-(.+)\.md$/);
  if (!m) continue; // skips _TEMPLATE.md
  const [, num, rest] = m;
  const { rawTitle, body } = split(fs.readFileSync(path.join(lessonsDir, f), 'utf8'));
  if (rest.includes('שיעורי-בית')) {
    homeworkBodies[num] = body;
    continue;
  }
  const { body: lessonBody, meta } = extractLessonMeta(body);
  const title = cleanTitle(rawTitle);
  const division = meta.division ?? divisionOf(Number(num));
  const hasHomework = fs.existsSync(path.join(lessonsDir, `${num}-שיעורי-בית.md`));
  write(
    path.join(docsOut, 'lessons', `lesson-${num}`, 'index.md'),
    {
      title,
      description: meta.note,
      kind: 'lesson',
      lesson: num,
      division,
      schedule: meta.schedule,
      demo: meta.demo ? `${GH_BASE}/${meta.demo}` : undefined,
      hasHomework: hasHomework ? 'yes' : undefined,
      github: `${GH_BASE}/lessons/${encodeURI(f)}`,
    },
    lessonBody,
  );
  courseData.lessons.push({
    num,
    title,
    division,
    note: meta.note ?? '',
    schedule: meta.schedule ?? [],
    hasHomework,
    slug: `/docs/lessons/lesson-${num}`,
  });
}
courseData.lessons.sort((a, b) => a.num.localeCompare(b.num));

// homework pages (need the lesson title)
for (const [num, body] of Object.entries(homeworkBodies)) {
  const lesson = courseData.lessons.find((l) => l.num === num);
  write(
    path.join(docsOut, 'lessons', `lesson-${num}`, 'homework.md'),
    { title: 'שיעורי בית', description: lesson ? `שיעור ${num} · ${lesson.title}` : `שיעור ${num}`, kind: 'homework', lesson: num, github: `${GH_BASE}/lessons/${encodeURI(`${num}-שיעורי-בית.md`)}` },
    body,
  );
}

for (const l of courseData.lessons) {
  fs.writeFileSync(
    path.join(docsOut, 'lessons', `lesson-${l.num}`, 'meta.json'),
    JSON.stringify({ title: `${l.num}. ${l.title}`, pages: l.hasHomework ? ['index', 'homework'] : ['index'] }, null, 2),
  );
}

const lessonPages = [];
let lastDiv = 0;
for (const l of courseData.lessons) {
  if (l.division !== lastDiv) {
    lessonPages.push(`---${divisionLabels[l.division]}---`);
    lastDiv = l.division;
  }
  lessonPages.push(`lesson-${l.num}`);
}
fs.writeFileSync(
  path.join(docsOut, 'lessons', 'meta.json'),
  JSON.stringify({ title: 'שיעורים', defaultOpen: true, pages: lessonPages }, null, 2),
);

// projects
const projectsDir = path.join(courseRoot, 'projects');
for (const f of fs.readdirSync(projectsDir).filter((f) => f.endsWith('.md'))) {
  const name = f.replace(/\.md$/, '');
  const slug = projectSlugs[name];
  if (!slug) continue;
  const { rawTitle, body } = split(fs.readFileSync(path.join(projectsDir, f), 'utf8'));
  const isGuide = slug.endsWith('-guide');
  const full = cleanTitle(rawTitle).replace(/^דף הנחיה \|\s*/, 'דף הנחיה · ');
  // keep the Hebrew part as the title and the English product name as subtitle (avoids mixed-direction titles)
  const split2 = full.match(/^(.*?פרויקט \d(?:\s*\([^)]*\))?)\s*[·–|-]\s*(.+)$/);
  const title = split2 ? split2[1] : full;
  const description = split2 ? split2[2] : '';
  write(path.join(docsOut, 'projects', `${slug}.md`), { title, description, kind: 'project' }, body);
  courseData.projects.push({ slug: `/docs/projects/${slug}`, title, description, isGuide });
}
// project 1's student guide lives next to the bot code in service-bot/
const bot1Guide = path.join(courseRoot, 'service-bot', 'דף-הנחיה-לסטודנטים.md');
if (fs.existsSync(bot1Guide)) {
  const { body } = split(fs.readFileSync(bot1Guide, 'utf8'));
  write(
    path.join(docsOut, 'projects', 'project-01-guide.md'),
    { title: 'דף הנחיה · פרויקט 1', description: 'Customer Service Bot', kind: 'project' },
    body,
  );
  courseData.projects.push({ slug: '/docs/projects/project-01-guide', title: 'דף הנחיה · פרויקט 1', description: 'Customer Service Bot', isGuide: true });
}
courseData.projects.sort((a, b) => a.slug.localeCompare(b.slug));
fs.writeFileSync(
  path.join(docsOut, 'projects', 'meta.json'),
  JSON.stringify(
    {
      title: 'פרויקטים',
      defaultOpen: true,
      // each project's spec sits next to its guidance page; project 1 has its guidance inside the spec
      pages: ['1', '2', '3'].flatMap((n) =>
        [`---פרויקט ${n}---`, `project-0${n}`, `project-0${n}-guide`].filter(
          (p) => p.startsWith('---') || courseData.projects.some((x) => x.slug.endsWith(`/${p}`)),
        ),
      ),
    },
    null,
    2,
  ),
);

const NL = String.fromCharCode(10);
// seed rows for lessons + assignments (re-runnable: upserts)
const sql = (t) => `'${t.replace(/'/g, "''")}'`;
const seed = [
  '-- Generated by scripts/sync-content.mjs. Safe to re-run.',
  'insert into public.lessons (id, title) values',
  courseData.lessons.map((l) => `  (${Number(l.num)}, ${sql(l.title)})`).join(',' + NL),
  'on conflict (id) do update set title = excluded.title;',
  '',
  'insert into public.assignments (id, lesson_id, kind, title) values',
  [
    ...courseData.lessons
      .filter((l) => l.hasHomework)
      .map((l) => `  (${Number(l.num)}, ${Number(l.num)}, 'homework', ${sql(`שיעורי בית ${l.num}`)})`),
    ...courseData.projects
      .filter((p) => !p.isGuide)
      .map((p, i) => `  (${101 + i}, null, 'project', ${sql(p.title)})`),
  ].join(',' + NL),
  'on conflict (id) do update set title = excluded.title;',
  '',
].join(NL);
fs.mkdirSync(path.join(siteRoot, 'supabase'), { recursive: true });
fs.writeFileSync(path.join(siteRoot, 'supabase', 'seed.sql'), seed);

fs.writeFileSync(path.join(siteRoot, 'src', 'lib', 'course.json'), JSON.stringify(courseData, null, 2));

// static assets
fs.mkdirSync(path.join(publicOut, 'assets'), { recursive: true });
fs.mkdirSync(path.join(publicOut, 'slides'), { recursive: true });
const assetsDir = path.join(courseRoot, 'assets');
for (const f of fs.readdirSync(assetsDir)) {
  if (/\.(png|svg)$/i.test(f)) fs.copyFileSync(path.join(assetsDir, f), path.join(publicOut, 'assets', f));
  if (f === '01-שקפים.html') fs.copyFileSync(path.join(assetsDir, f), path.join(publicOut, 'slides', '01.html'));
}

// lesson 07 references assets/mcp-client-tools-flow.png, which only exists as mcp-flow.png in the course root
const mcpFallback = path.join(courseRoot, 'mcp-flow.png');
const mcpTarget = path.join(publicOut, 'assets', 'mcp-client-tools-flow.png');
if (!fs.existsSync(mcpTarget) && fs.existsSync(mcpFallback)) fs.copyFileSync(mcpFallback, mcpTarget);

console.log(`synced ${courseData.lessons.length} lessons, ${courseData.projects.length} projects`);
