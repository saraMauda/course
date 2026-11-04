import type { ViewCell } from '@/lib/notebook';

/** Read-only rendering of a submitted notebook: titles, code and what each cell printed. */
export function NotebookView({ cells }: { cells: ViewCell[] }) {
  return (
    <div className="space-y-3">
      {cells.map((c, i) =>
        c.type === 'code' ? (
          <section key={i} className="overflow-hidden rounded-xl border">
            <pre dir="ltr" className="overflow-x-auto bg-fd-background p-4 font-mono text-sm leading-6">
              {c.source || ' '}
            </pre>
            {c.outputs.map((o, j) =>
              o.kind === 'image' ? (
                <div key={j} className="border-t bg-fd-muted/40 p-4">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={o.src} alt="פלט גרפי של התא" className="max-w-full" />
                </div>
              ) : (
                <pre
                  key={j}
                  dir="auto"
                  className={`whitespace-pre-wrap break-words border-t bg-fd-muted/40 p-4 text-sm ${o.kind === 'error' ? 'text-red-600' : ''}`}
                >
                  {o.text}
                </pre>
              ),
            )}
            {!c.outputs.length && <p className="border-t bg-fd-muted/40 px-4 py-2 text-xs text-fd-muted-foreground">אין פלט (התא לא הורץ או שלא הדפיס כלום)</p>}
          </section>
        ) : (
          <p key={i} dir="auto" className={`whitespace-pre-wrap px-1 ${c.type === 'markdown' ? 'font-semibold' : 'text-fd-muted-foreground'}`}>
            {c.source.replace(/^#+\s*/gm, '')}
          </p>
        ),
      )}
    </div>
  );
}
