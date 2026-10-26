'use client';

import { useState } from 'react';
import { createClient } from '@/lib/supabase/client';
import type { ProjectItem } from '@/lib/project-items';

export interface ItemView {
  item: ProjectItem;
  text?: string;
  url?: string;
  isImage?: boolean;
}

// One tickbox per delivery item; each tick is saved immediately.
export function ItemChecks({
  submissionId,
  views,
  initial,
}: {
  submissionId: number;
  views: ItemView[];
  initial: Record<string, boolean>;
}) {
  const [checks, setChecks] = useState(initial);
  const [error, setError] = useState('');

  async function toggle(key: string, ok: boolean) {
    setError('');
    setChecks((c) => ({ ...c, [key]: ok }));
    const supabase = createClient();
    const { error } = ok
      ? await supabase.from('submission_checks').upsert({ submission_id: submissionId, item_key: key, ok: true })
      : await supabase.from('submission_checks').delete().eq('submission_id', submissionId).eq('item_key', key);
    if (error) {
      setChecks((c) => ({ ...c, [key]: !ok }));
      setError('השמירה נכשלה');
    }
  }

  const done = views.filter((v) => checks[v.item.key]).length;
  return (
    <div className="space-y-2">
      <div className="text-sm font-medium">
        סימון פריטים · {done}/{views.length}
      </div>
      <ul className="space-y-2">
        {views.map(({ item, text, url, isImage }) => (
          <li key={item.key} className="rounded-lg border p-2.5 text-sm">
            <label className="flex cursor-pointer items-start gap-2">
              <input
                type="checkbox"
                className="mt-1 size-4 shrink-0"
                checked={Boolean(checks[item.key])}
                onChange={(e) => toggle(item.key, e.target.checked)}
              />
              <span className="font-medium">{item.label}</span>
            </label>
            <div className="mt-1.5 space-y-1 ps-6">
              {!text && !url && <span className="text-red-600">לא הוגש</span>}
              {text &&
                (/^https?:\/\//i.test(text) ? (
                  <a href={text} target="_blank" rel="noreferrer" dir="ltr" className="block break-all text-fd-primary underline">
                    {text}
                  </a>
                ) : (
                  <p className="whitespace-pre-wrap text-fd-muted-foreground">{text}</p>
                ))}
              {url && isImage && (
                <a href={url} target="_blank" rel="noreferrer" className="block">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={url} alt={item.label} className="max-h-56 rounded-lg border" />
                </a>
              )}
              {url && !isImage && (
                <a href={url} target="_blank" rel="noreferrer" className="inline-block rounded-lg border px-3 py-1 hover:bg-fd-accent">
                  הקובץ שהוגש
                </a>
              )}
            </div>
          </li>
        ))}
      </ul>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
