import { describe, expect, it } from 'vitest';
import { splitPipLines, toIpynb } from './py-notebook';

describe('toIpynb', () => {
  it('writes a markdown title and a code cell per cell, with newline-terminated source lines', () => {
    const nb = JSON.parse(toIpynb([{ title: 'תא 1', code: 'a = 1\nprint(a)' }]));
    expect(nb.nbformat).toBe(4);
    expect(nb.cells).toHaveLength(2);
    expect(nb.cells[0]).toMatchObject({ cell_type: 'markdown', source: ['## תא 1'] });
    expect(nb.cells[1]).toMatchObject({ cell_type: 'code', source: ['a = 1\n', 'print(a)'] });
  });
});

describe('splitPipLines', () => {
  it('removes pip lines and sorts packages into builtin, unsupported and installable', () => {
    const r = splitPipLines('!pip install -q cohere gradio numpy requests==2.0\nprint(1)');
    expect(r.code).toBe('print(1)');
    expect(r.builtin).toEqual(['cohere', 'numpy']);
    expect(r.unsupported).toEqual(['gradio']);
    expect(r.packages).toEqual(['requests==2.0']);
  });
  it('accepts the %pip form and leaves other lines alone', () => {
    const r = splitPipLines('x = 1\n%pip install tqdm\ny = 2');
    expect(r.code).toBe('x = 1\ny = 2');
    expect(r.packages).toEqual(['tqdm']);
  });
  it('does not treat a string mentioning pip as an install', () => {
    const r = splitPipLines('print("!pip install foo")');
    expect(r.code).toBe('print("!pip install foo")');
    expect(r.packages).toEqual([]);
  });
});
