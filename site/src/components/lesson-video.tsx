'use client';

import { useEffect, useState } from 'react';
import { ExternalLink, FolderOpen } from 'lucide-react';
import { createClient } from '@/lib/supabase/client';
import { parseDriveLink, type DriveLink } from '@/lib/drive';

const configured = Boolean(process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);

/** The lesson recording. Renders nothing until the teacher adds a Drive link at /admin/lessons. */
export function LessonVideo({ lesson }: { lesson: string }) {
  const [link, setLink] = useState<DriveLink | null>(null);

  useEffect(() => {
    if (!configured) return;
    let active = true;
    createClient()
      .from('lessons')
      .select('video_url')
      .eq('id', Number(lesson))
      .maybeSingle()
      .then(({ data }) => {
        if (active) setLink(parseDriveLink(data?.video_url));
      });
    return () => {
      active = false;
    };
  }, [lesson]);

  if (!link) return null;

  return (
    <section className="mb-6 space-y-3" aria-labelledby="lesson-video-title">
      <h2 id="lesson-video-title" className="text-lg font-semibold">
        סרטון השיעור
      </h2>
      {link.embed && (
        <iframe
          src={link.embed}
          title={`סרטון שיעור ${lesson}`}
          className="aspect-video w-full rounded-xl border bg-fd-muted"
          allow="autoplay; fullscreen"
          allowFullScreen
          loading="lazy"
        />
      )}
      <a
        href={link.url}
        target="_blank"
        rel="noreferrer"
        className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors hover:bg-fd-accent"
      >
        {link.embed ? <ExternalLink className="size-4" /> : <FolderOpen className="size-4" />}
        {link.embed ? 'הסרטון לא נטען? פתיחה ב-Drive' : 'סרטוני השיעור ב-Drive'}
      </a>
    </section>
  );
}
