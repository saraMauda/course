import { describe, expect, it } from 'vitest';
import { isNotebookPath, parseNotebook, STORAGE_PATH } from './notebook';
import { toIpynb } from './py-notebook';

describe('parseNotebook', () => {
  it('round-trips what the playground exports, with output and error', () => {
    const cells = parseNotebook(
      toIpynb([
        { title: 'תא 1', code: 'print(1)', output: '1\n' },
        { title: 'תא 2', code: 'boom()', error: 'NameError: boom' },
      ]),
    )!;
    expect(cells.map((c) => c.type)).toEqual(['markdown', 'code', 'markdown', 'code']);
    expect(cells[1]).toMatchObject({ source: 'print(1)', outputs: [{ kind: 'text', text: '1\n' }] });
    expect(cells[3].outputs).toEqual([{ kind: 'error', text: 'NameError: boom' }]);
  });
  it('reads a Colab-style notebook: images only as verified base64 PNG, never html', () => {
    const nb = {
      cells: [
        {
          cell_type: 'code',
          source: ['x = 1\n', 'x'],
          outputs: [
            { output_type: 'execute_result', data: { 'text/plain': ['1'], 'text/html': ['<script>alert(1)</script>'] } },
            { output_type: 'display_data', data: { 'image/png': 'iVBORw0KGgo=' } },
            { output_type: 'display_data', data: { 'image/png': '" onerror="alert(1)' } },
            { output_type: 'error', ename: 'E', evalue: 'v', traceback: ['\u001b[31mred\u001b[0m'] },
          ],
        },
      ],
    };
    const [c] = parseNotebook(JSON.stringify(nb))!;
    expect(c.source).toBe('x = 1\nx');
    expect(c.outputs).toEqual([
      { kind: 'text', text: '1' },
      { kind: 'image', src: 'data:image/png;base64,iVBORw0KGgo=' },
      { kind: 'error', text: 'red' },
    ]);
  });
  it('rejects things that are not notebooks', () => {
    expect(parseNotebook('nope')).toBeNull();
    expect(parseNotebook('{"a":1}')).toBeNull();
  });
});

describe('storage paths', () => {
  it('accepts <uuid>/<assignment>/<file> and nothing that climbs or nests further', () => {
    const id = '123e4567-e89b-12d3-a456-426614174000';
    expect(STORAGE_PATH.test(`${id}/101/run-1.ipynb`)).toBe(true);
    expect(STORAGE_PATH.test(`${id}/101/../x.ipynb`)).toBe(false);
    expect(STORAGE_PATH.test(`${id}/101/a/b.ipynb`)).toBe(false);
    expect(STORAGE_PATH.test('other/101/x.ipynb')).toBe(false);
    expect(isNotebookPath('a/b/run.IPYNB')).toBe(true);
    expect(isNotebookPath('a/b/run.py')).toBe(false);
  });
});
