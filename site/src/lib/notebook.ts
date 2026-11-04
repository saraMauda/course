// Read-only view model of a Jupyter notebook (.ipynb), for the teacher to review a submitted one.

export type ViewOutput = { kind: 'text' | 'error'; text: string } | { kind: 'image'; src: string };
export interface ViewCell {
  type: 'markdown' | 'code' | 'raw';
  source: string;
  outputs: ViewOutput[];
}

const ANSI = /\u001b\[[0-9;]*m/g;
const BASE64 = /^[A-Za-z0-9+/=\s]+$/;

const asText = (v: unknown): string => (Array.isArray(v) ? v.join('') : typeof v === 'string' ? v : '');

function parseOutput(o: Record<string, unknown>): ViewOutput | null {
  switch (o.output_type) {
    case 'stream':
      return { kind: 'text', text: asText(o.text) };
    case 'error': {
      const trace = Array.isArray(o.traceback) ? o.traceback.join('\n') : '';
      return { kind: 'error', text: (trace || `${o.ename}: ${o.evalue}`).replace(ANSI, '') };
    }
    case 'execute_result':
    case 'display_data': {
      const data = (o.data ?? {}) as Record<string, unknown>;
      const png = asText(data['image/png']);
      // only a verified base64 PNG becomes an <img>; HTML/JS outputs are never rendered
      if (png && BASE64.test(png)) return { kind: 'image', src: `data:image/png;base64,${png.replace(/\s/g, '')}` };
      const text = asText(data['text/plain']);
      return text ? { kind: 'text', text } : null;
    }
    default:
      return null;
  }
}

/** Parses notebook JSON. Returns null when it is not a notebook. */
export function parseNotebook(json: string): ViewCell[] | null {
  let nb: unknown;
  try {
    nb = JSON.parse(json);
  } catch {
    return null;
  }
  const cells = (nb as { cells?: unknown })?.cells;
  if (!Array.isArray(cells)) return null;
  return cells.map((c: Record<string, unknown>) => ({
    type: c.cell_type === 'code' || c.cell_type === 'markdown' ? c.cell_type : 'raw',
    source: asText(c.source),
    outputs: Array.isArray(c.outputs)
      ? c.outputs.map((o) => parseOutput(o as Record<string, unknown>)).filter((o): o is ViewOutput => o !== null)
      : [],
  }));
}

/** Storage paths are `<student uuid>/<assignment id>/<file>`; anything else is rejected before touching storage. */
export const STORAGE_PATH = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\/\d+\/[\w.-]+$/i;
export const isNotebookPath = (p: string | null | undefined): p is string => Boolean(p && /\.ipynb$/i.test(p));
