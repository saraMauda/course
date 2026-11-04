/** Packages the in-browser runtime already provides (or replaces with its own shim), so `pip install` skips them. */
export const BUILTIN_PACKAGES = new Set(['numpy', 'cohere']);
/** Packages that cannot run in the browser at all. */
export const UNSUPPORTED_PACKAGES = new Set(['gradio']);

export interface PipSplit {
  code: string;
  packages: string[];
  builtin: string[];
  unsupported: string[];
}

const PIP_LINE = /^\s*[!%]pip\s+install\s+(.*)$/;

/** Pulls `!pip install ...` lines out of a cell, because Pyodide installs packages through micropip instead. */
export function splitPipLines(source: string): PipSplit {
  const packages: string[] = [];
  const builtin: string[] = [];
  const unsupported: string[] = [];
  const kept: string[] = [];

  for (const line of source.split('\n')) {
    const m = PIP_LINE.exec(line);
    if (!m) {
      kept.push(line);
      continue;
    }
    for (const arg of m[1].split(/\s+/)) {
      if (!arg || arg.startsWith('-')) continue;
      const name = arg.split(/[=<>~![;]/)[0].toLowerCase();
      if (BUILTIN_PACKAGES.has(name)) builtin.push(name);
      else if (UNSUPPORTED_PACKAGES.has(name)) unsupported.push(name);
      else packages.push(arg);
    }
  }
  return { code: kept.join('\n'), packages, builtin, unsupported };
}

export interface NotebookCell {
  id: string;
  title: string;
  code: string;
}

/** Serialises cells as a Jupyter notebook (nbformat 4), so the student can submit a normal .ipynb. */
export function toIpynb(cells: { title: string; code: string; output?: string; error?: string }[]): string {
  const lines = (s: string) => s.split('\n').map((l, i, a) => (i < a.length - 1 ? l + '\n' : l));
  // what the cell printed (and its error, if any) travels with the notebook so the teacher sees the results
  const outputs = (c: { output?: string; error?: string }) => [
    ...(c.output ? [{ output_type: 'stream', name: 'stdout', text: lines(c.output) }] : []),
    ...(c.error ? [{ output_type: 'error', ename: 'Error', evalue: '', traceback: [c.error] }] : []),
  ];
  return JSON.stringify(
    {
      nbformat: 4,
      nbformat_minor: 5,
      metadata: { language_info: { name: 'python' } },
      cells: cells.flatMap((c, i) => [
        { cell_type: 'markdown', id: `m${i}`, metadata: {}, source: [`## ${c.title}`] },
        { cell_type: 'code', id: `c${i}`, metadata: {}, execution_count: null, outputs: outputs(c), source: lines(c.code) },
      ]),
    },
    null,
    1,
  );
}
