import { RootProvider } from 'fumadocs-ui/provider/next';
import './global.css';
import { Heebo } from 'next/font/google';

export const metadata = {
  title: { default: 'Agentic AI', template: '%s | Agentic AI' },
  description: 'חומרי הקורס, קוד ושיעורי בית',
};

const heebo = Heebo({
  subsets: ['hebrew', 'latin'],
});

export default function Layout({ children }: LayoutProps<'/'>) {
  return (
    <html lang="he" dir="rtl" className={heebo.className} suppressHydrationWarning>
      <body className="flex flex-col min-h-screen">
        <RootProvider
          i18n={{
            locale: 'he',
            translations: {
              search: 'חיפוש',
              searchNoResult: 'לא נמצאו תוצאות',
              toc: 'בעמוד זה',
              tocNoHeadings: 'אין כותרות',
              lastUpdate: 'עודכן לאחרונה',
              chooseLanguage: 'בחירת שפה',
              nextPage: 'הבא',
              previousPage: 'הקודם',
              chooseTheme: 'ערכת נושא',
              editOnGithub: 'עריכה ב-GitHub',
            },
          }}
        >
          {children}
        </RootProvider>
      </body>
    </html>
  );
}
