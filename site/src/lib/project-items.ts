// The delivery checklist of each project (mirrors "Checklist מסירה" in the project specs).
// kind: what the student attaches for the item. 'link' = URL, 'text' = free text, 'file' = upload (image/zip/py...).
export interface ProjectItem {
  key: string;
  label: string;
  kind: 'link' | 'text' | 'file';
  optional?: boolean;
}

export const projectItems: Record<number, { assignmentId: number; title: string; items: ProjectItem[] }> = {
  1: {
    assignmentId: 101,
    title: 'פרויקט 1',
    items: [
      { key: 'repo', label: 'קישור למאגר Git (כולל README: תחום, הרצה, משתני סביבה)', kind: 'link' },
      { key: 'data', label: 'קובץ data + קובץ הווקטורים .npy (או סקריפט בניה)', kind: 'file' },
      { key: 'run', label: 'סקריפט / notebook להרצה', kind: 'file' },
      { key: 'tests', label: 'לפחות 8 מקרי בדיקה: 5 פגיעה טובה, 2 ניסוח חלופי, 1 מחוץ לתחום', kind: 'file' },
      { key: 'json', label: 'דוגמת פלט מובנה אחד (JSON)', kind: 'text' },
      { key: 'screenshot', label: 'צילום מסך של ממשק ה-Gradio', kind: 'file' },
    ],
  },
  2: {
    assignmentId: 102,
    title: 'פרויקט 2',
    items: [
      { key: 'repo', label: 'קישור למאגר Git (README: APIs, MCP, איך להריץ, דוגמת session)', kind: 'link' },
      { key: 'chats', label: 'לפחות 2 שיחות רב-הודעתיות (זיכרון עובד)', kind: 'file' },
      { key: 'toollog', label: 'לוג tool calls (מה הופעל ולמה)', kind: 'file' },
      { key: 'queries', label: '3 שאילתות מחקר שונות + מקורות בפלט', kind: 'file' },
      { key: 'rot', label: 'תיאור: איך נמנעתם מ-Context Rot', kind: 'text' },
    ],
  },
  3: {
    assignmentId: 103,
    title: 'פרויקט 3',
    items: [
      { key: 'repo', label: 'קישור למאגר Git (README: ארכיטקטורה, הרצה, env vars, דיאגרמת גרף)', kind: 'link' },
      { key: 'sources', label: 'לפחות 3 מקורות באינדקס במחברת דמו', kind: 'file' },
      { key: 'approve', label: 'זרימת Approve: pending → approved → searchable', kind: 'file' },
      { key: 'chat', label: 'שיחה: שאלה מכוסה + שאלה מחוץ למקורות', kind: 'file' },
      { key: 'tool', label: 'tool חיצוני אחד לפחות (מופעל ב-trace)', kind: 'text' },
      { key: 'thread', label: 'thread_id: המשך שיחה עם זיכרון', kind: 'file' },
      { key: 'trace', label: 'קישור / צילום trace מ-LangSmith', kind: 'link' },
      { key: 'guard', label: 'Guardrails: לא להמציא מתוך ידע כללי כשיש מקורות', kind: 'text' },
    ],
  },
};
