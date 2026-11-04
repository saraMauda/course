import { HomeLayout } from 'fumadocs-ui/layouts/home';
import { baseOptions } from '@/lib/layout.shared';
import { PythonNotebook } from '@/components/python-notebook';
import { project1Cells } from '@/lib/project1-cells';
import { projectItems } from '@/lib/project-items';

export const metadata = {
  title: 'סביבת הרצה · פרויקט 1',
  description: 'מריצים את קוד פרויקט 1 בתוך האתר, בלי Colab ובלי חשבון גוגל',
  robots: { index: false, follow: false },
};

export default function PlaygroundPage() {
  return (
    <HomeLayout {...baseOptions()}>
      <main className="mx-auto w-full max-w-3xl space-y-6 p-6">
        <header className="space-y-2">
          <h1 className="text-2xl font-bold">סביבת הרצה: פרויקט 1</h1>
          <p className="text-fd-muted-foreground">
            הקוד רץ בדפדפן שלך. מדביקים מפתח Cohere, מעלים את <code dir="ltr">dataset.json</code>, ומריצים את התאים לפי הסדר
            (<kbd dir="ltr">Shift + Enter</kbd> בתוך תא). הסבר על כל שלב נמצא ב
            <a className="text-fd-primary underline" href="/docs/projects/project-01-guide">דף ההנחיה</a>.
          </p>
        </header>
        <PythonNotebook
          cells={project1Cells}
          storageKey="py-notebook-project1"
          submitTo={{ assignmentId: projectItems[1].assignmentId, itemKey: 'run', projectHref: '/docs/projects/project-01' }}
        />
      </main>
    </HomeLayout>
  );
}
