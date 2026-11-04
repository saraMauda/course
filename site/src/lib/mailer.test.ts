import { describe, expect, it } from 'vitest';
import { buildCustomMail, buildSubmissionMail, escapeHtml } from './mailer';

describe('buildCustomMail', () => {
  it('keeps the text as written, links URLs and escapes html', () => {
    const m = buildCustomMail('נושא', 'היי <b>\nhttps://a.co/x?y=1&z=2');
    expect(m.text).toBe('היי <b>\nhttps://a.co/x?y=1&z=2');
    expect(m.html).toContain('&lt;b&gt;');
    expect(m.html).toContain('<a href="https://a.co/x?y=1&amp;z=2">');
  });
});

describe('buildSubmissionMail', () => {
  it('returned: mentions the assignment and includes feedback', () => {
    const m = buildSubmissionMail({ event: 'returned', studentName: 'דנה', assignmentTitle: 'פרויקט 1', feedback: 'חסר README' });
    expect(m.subject).toContain('הוחזרה לתיקון');
    expect(m.text).toContain('היי דנה,');
    expect(m.text).toContain('חסר README');
    expect(m.html).toContain('dir="rtl"');
  });
  it('graded: shows the grade', () => {
    const m = buildSubmissionMail({ event: 'graded', studentName: '', assignmentTitle: 'שיעורי בית 2', grade: 95 });
    expect(m.text).toContain('ציון: 95');
    expect(m.text.startsWith('שלום,')).toBe(true);
  });
  it('escapes html in teacher feedback', () => {
    const m = buildSubmissionMail({ event: 'returned', studentName: 'x', assignmentTitle: 't', feedback: '<script>alert(1)</script>' });
    expect(m.html).not.toContain('<script>');
    expect(escapeHtml('a&b')).toBe('a&amp;b');
  });
});
