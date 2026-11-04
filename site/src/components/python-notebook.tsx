'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { splitPipLines, toIpynb, type NotebookCell } from '@/lib/py-notebook';

interface CellState {
  code: string;
  output: string;
  error: string;
  ran: boolean;
}
interface FileInfo {
  name: string;
  size: number;
}
type Status = 'loading' | 'ready' | 'failed';

const KEY_NAME = 'COHERE_API_KEY';
const store = {
  get(area: 'local' | 'session', k: string) {
    try {
      return (area === 'local' ? localStorage : sessionStorage).getItem(k);
    } catch {
      return null;
    }
  },
  set(area: 'local' | 'session', k: string, v: string) {
    try {
      (area === 'local' ? localStorage : sessionStorage).setItem(k, v);
    } catch {
      /* private mode or blocked storage: the notebook still works, it just will not remember */
    }
  },
};

function initialCells(cells: NotebookCell[], storageKey: string): Record<string, CellState> {
  let saved: Record<string, string> = {};
  try {
    saved = JSON.parse(store.get('local', storageKey) ?? '{}');
  } catch {
    /* corrupt value: start from the defaults */
  }
  return Object.fromEntries(
    cells.map((c) => [c.id, { code: saved[c.id] ?? c.code, output: '', error: '', ran: false }]),
  );
}

const btn = 'rounded-lg border px-3 py-1.5 text-sm font-medium hover:bg-fd-accent disabled:opacity-50';
const primary = 'rounded-lg bg-fd-primary px-3 py-1.5 text-sm font-medium text-fd-primary-foreground disabled:opacity-50';

export function PythonNotebook({ cells, storageKey }: { cells: NotebookCell[]; storageKey: string }) {
  const [state, setState] = useState<Record<string, CellState>>(() => initialCells(cells, storageKey));
  const [status, setStatus] = useState<Status>('loading');
  const [statusText, setStatusText] = useState('');
  const [running, setRunning] = useState<string | null>(null);
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [apiKey, setApiKey] = useState('');

  const worker = useRef<Worker | null>(null);
  const waiting = useRef(new Map<string, (ok: boolean) => void>());
  const apiKeyRef = useRef('');
  const stopped = useRef(false);

  const patch = useCallback((id: string, p: Partial<CellState> | ((c: CellState) => Partial<CellState>)) => {
    setState((s) => ({ ...s, [id]: { ...s[id], ...(typeof p === 'function' ? p(s[id]) : p) } }));
  }, []);

  const sendKey = useCallback((value: string) => {
    worker.current?.postMessage({ type: 'secrets', value: { [KEY_NAME]: value } });
  }, []);

  const start = useCallback(() => {
    worker.current?.terminate();
    waiting.current.forEach((resolve) => resolve(false));
    waiting.current.clear();
    setStatus('loading');
    setRunning(null);

    const w = new Worker('/pyodide-worker.js');
    worker.current = w;
    w.onmessage = ({ data }) => {
      switch (data.type) {
        case 'status':
          setStatusText(data.text);
          break;
        case 'ready':
          setStatus('ready');
          setStatusText('');
          sendKey(apiKeyRef.current);
          w.postMessage({ type: 'listFiles' });
          break;
        case 'stdout':
          patch(data.id, (c) => ({ output: c.output + data.text + '\n' }));
          break;
        case 'done':
          patch(data.id, { error: data.error ?? '', ran: true });
          waiting.current.get(data.id)?.(!data.error);
          waiting.current.delete(data.id);
          w.postMessage({ type: 'listFiles' });
          break;
        case 'files':
          setFiles(data.files);
          break;
        case 'file': {
          const url = URL.createObjectURL(new Blob([data.data]));
          const a = document.createElement('a');
          a.href = url;
          a.download = data.name;
          a.click();
          URL.revokeObjectURL(url);
          break;
        }
        case 'fatal':
          setStatus('failed');
          setStatusText(data.text);
          break;
      }
    };
    w.onerror = () => {
      setStatus('failed');
      setStatusText('טעינת פייתון נכשלה. בדקי חיבור לאינטרנט ורענני את הדף.');
    };
    w.postMessage({ type: 'init' });
  }, [patch, sendKey]);

  useEffect(() => {
    apiKeyRef.current = store.get('session', 'py-api-key') ?? '';
    setApiKey(apiKeyRef.current);
    stopped.current = false;
    start();
    return () => {
      stopped.current = true;
      worker.current?.terminate();
    };
  }, [start]);

  const runCell = useCallback(
    (id: string) =>
      new Promise<boolean>((resolve) => {
        const w = worker.current;
        if (!w) return resolve(false);
        const { code, packages, builtin, unsupported } = splitPipLines(state[id].code);
        const notes = [
          builtin.length && `${builtin.join(', ')}: כבר מותקן באתר, אין צורך להתקין.`,
          unsupported.length && `${unsupported.join(', ')}: לא רץ בדפדפן. את הממשק מריצים בתא הניסוי.`,
        ].filter(Boolean);
        patch(id, { output: notes.map((n) => n + '\n').join(''), error: '', ran: false });
        setRunning(id);
        waiting.current.set(id, (ok) => {
          setRunning((r) => (r === id ? null : r));
          resolve(ok);
        });
        w.postMessage({ type: 'run', id, code, packages });
      }),
    [state, patch],
  );

  async function runAll() {
    for (const c of cells) {
      // stop at the first failure, the same way a student would
      const ok = await runCell(c.id);
      if (!ok || stopped.current) return;
    }
  }

  function edit(id: string, code: string) {
    patch(id, { code });
    const saved = Object.fromEntries(cells.map((c) => [c.id, c.id === id ? code : state[c.id].code]));
    store.set('local', storageKey, JSON.stringify(saved));
  }

  function downloadNotebook() {
    const json = toIpynb(cells.map((c) => ({ title: c.title, code: state[c.id].code })));
    const url = URL.createObjectURL(new Blob([json], { type: 'application/x-ipynb+json' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = 'service-bot.ipynb';
    a.click();
    URL.revokeObjectURL(url);
  }

  function reset() {
    if (!window.confirm('לאפס את התאים לקוד המקורי ולהתחיל סשן חדש? הקבצים שהועלו יימחקו.')) return;
    try {
      localStorage.removeItem(storageKey);
    } catch {
      /* nothing stored */
    }
    setState(initialCells(cells, storageKey));
    setFiles([]);
    start();
  }

  async function upload(list: FileList | null) {
    if (!list) return;
    for (const f of Array.from(list)) {
      worker.current?.postMessage({ type: 'writeFile', name: f.name.replace(/[^\w.\-]/g, '_'), data: await f.arrayBuffer() });
    }
  }

  const ready = status === 'ready';
  const input = 'rounded-lg border bg-fd-background px-3 py-1.5 text-sm';

  return (
    <div className="space-y-6">
      <section className="rounded-xl border bg-fd-card p-4 space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <span
            role="status"
            className={`inline-flex items-center gap-2 text-sm ${status === 'failed' ? 'text-red-600' : 'text-fd-muted-foreground'}`}
          >
            <span className={`size-2 rounded-full ${ready ? 'bg-green-500' : status === 'failed' ? 'bg-red-500' : 'bg-amber-500 animate-pulse'}`} />
            {ready ? 'פייתון מוכן' : statusText || 'טוען...'}
          </span>
          <div className="ms-auto flex gap-2">
            <button className={primary} disabled={!ready || running !== null} onClick={runAll}>
              הרצת כל התאים
            </button>
            <button className={btn} onClick={downloadNotebook}>
              הורדת notebook
            </button>
            <button className={btn} onClick={reset}>
              איפוס
            </button>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block space-y-1">
            <span className="text-sm font-medium">מפתח Cohere</span>
            <input
              className={`${input} w-full`}
              dir="ltr"
              type="password"
              autoComplete="off"
              placeholder="הדביקי כאן את ה-Trial key"
              value={apiKey}
              onChange={(e) => {
                setApiKey(e.target.value);
                apiKeyRef.current = e.target.value;
                store.set('session', 'py-api-key', e.target.value);
                sendKey(e.target.value);
              }}
            />
            <span className="block text-xs text-fd-muted-foreground">
              נשמר רק בלשונית הזאת ונשלח רק ל-Cohere. נמחק כשסוגרים את הלשונית.
            </span>
          </label>

          <div className="space-y-1">
            <span className="text-sm font-medium">קבצים</span>
            <input className={`${input} w-full`} type="file" multiple disabled={!ready} onChange={(e) => upload(e.target.files)} />
            {files.length > 0 && (
              <ul className="text-sm space-y-1" dir="ltr">
                {files.map((f) => (
                  <li key={f.name} className="flex items-center justify-between gap-2">
                    <span className="truncate">
                      {f.name} <span className="text-fd-muted-foreground">({(f.size / 1024).toFixed(1)} KB)</span>
                    </span>
                    <button className="text-fd-primary underline" onClick={() => worker.current?.postMessage({ type: 'readFile', name: f.name })}>
                      הורדה
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </section>

      {cells.map((c) => {
        const s = state[c.id];
        return (
          <section key={c.id} className="rounded-xl border bg-fd-card overflow-hidden">
            <div className="flex items-center justify-between gap-2 border-b px-4 py-2">
              <h2 className="font-medium">{c.title}</h2>
              <button className={primary} disabled={!ready || running !== null} onClick={() => runCell(c.id)}>
                {running === c.id ? 'רץ...' : s.ran ? 'הרצה שוב' : 'הרצה'}
              </button>
            </div>
            <textarea
              dir="ltr"
              spellCheck={false}
              aria-label={c.title}
              className="block w-full resize-y bg-fd-background p-4 font-mono text-sm leading-6 outline-none"
              rows={Math.min(28, s.code.split('\n').length + 1)}
              value={s.code}
              onChange={(e) => edit(c.id, e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.shiftKey || e.ctrlKey) && ready && running === null) {
                  e.preventDefault();
                  runCell(c.id);
                }
              }}
            />
            {(s.output || s.error) && (
              <pre dir="auto" className="border-t bg-fd-muted/40 p-4 text-sm whitespace-pre-wrap break-words">
                {s.output}
                {s.error && <span className="text-red-600">{s.error}</span>}
              </pre>
            )}
          </section>
        );
      })}
    </div>
  );
}
