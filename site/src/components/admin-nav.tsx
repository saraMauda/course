'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { SignOutButton } from '@/components/sign-out-button';

const TABS = [
  { href: '/admin', label: 'סקירה ותלמידות', exact: true },
  { href: '/admin/submissions', label: 'הגשות', badge: true },
  { href: '/admin/attendance', label: 'נוכחות' },
  { href: '/admin/lessons', label: 'שיעורים ותאריכים' },
  { href: '/admin/email', label: 'מיילים' },
];

export function AdminNav({ pending }: { pending: number }) {
  const path = usePathname();
  return (
    <header className="sticky top-0 z-10 border-b bg-fd-background/95 backdrop-blur">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-x-4 gap-y-1 px-4 py-2">
        <nav aria-label="ניהול הקורס" className="flex flex-wrap gap-1">
          {TABS.map((t) => {
            const active = t.exact ? path === t.href || path.startsWith('/admin/students') : path.startsWith(t.href);
            return (
              <Link
                key={t.href}
                href={t.href}
                aria-current={active ? 'page' : undefined}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium ${active ? 'bg-fd-primary text-fd-primary-foreground' : 'hover:bg-fd-accent'}`}
              >
                {t.label}
                {t.badge && pending > 0 && (
                  <span className={`ms-1.5 rounded-full px-1.5 text-xs ${active ? 'bg-white/25' : 'bg-amber-500 text-white'}`}>{pending}</span>
                )}
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center gap-2">
          <Link href="/docs" className="rounded-lg px-3 py-1.5 text-sm font-medium hover:bg-fd-accent">
            חומרי הקורס
          </Link>
          <SignOutButton />
        </div>
      </div>
    </header>
  );
}
