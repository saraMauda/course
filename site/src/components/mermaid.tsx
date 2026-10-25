'use client';

import { useEffect, useId, useState } from 'react';
import { useTheme } from 'next-themes';

let counter = 0;

export function Mermaid({ chart }: { chart: string }) {
  const id = useId().replace(/:/g, '');
  const { resolvedTheme } = useTheme();
  const [svg, setSvg] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const mermaid = (await import('mermaid')).default;
      mermaid.initialize({
        startOnLoad: false,
        securityLevel: 'loose',
        theme: resolvedTheme === 'dark' ? 'dark' : 'default',
        fontFamily: 'inherit',
      });
      try {
        const { svg } = await mermaid.render(`m${id}-${++counter}`, chart);
        if (!cancelled) setSvg(svg);
      } catch {
        if (!cancelled) setSvg('');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [chart, id, resolvedTheme]);

  if (!svg) return <pre dir="ltr" className="text-sm opacity-60">{chart}</pre>;
  return <div dir="ltr" className="my-6 flex justify-center overflow-x-auto" dangerouslySetInnerHTML={{ __html: svg }} />;
}
