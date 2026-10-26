import { describe, expect, it } from 'vitest';
import { csvCell, toCsv } from './csv';

describe('csv', () => {
  it('leaves plain values alone and blanks null', () => {
    expect(csvCell('שלום')).toBe('שלום');
    expect(csvCell(12)).toBe('12');
    expect(csvCell(null)).toBe('');
  });
  it('quotes commas, quotes and newlines', () => {
    expect(csvCell('a,b')).toBe('"a,b"');
    expect(csvCell('say "hi"')).toBe('"say ""hi"""');
    expect(csvCell('a\nb')).toBe('"a\nb"');
  });
  it('defuses spreadsheet formulas in text', () => {
    expect(csvCell('=HYPERLINK("x")')).toBe(`"'=HYPERLINK(""x"")"`);
    expect(csvCell('+1')).toBe("'+1");
  });
  it('does not touch negative numbers', () => expect(csvCell(-5)).toBe('-5'));
  it('starts with a BOM and uses CRLF', () => {
    const out = toCsv([['a', 'b'], [1, 2]]);
    expect(out.startsWith('\uFEFF')).toBe(true);
    expect(out).toContain('a,b\r\n1,2\r\n');
  });
});
