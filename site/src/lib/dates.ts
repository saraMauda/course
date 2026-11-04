/** "יום שלישי, 3 בנובמבר" for a YYYY-MM-DD day. Noon UTC keeps the day stable in every time zone. */
export function hebrewDate(day: string) {
  return new Date(`${day}T12:00:00Z`).toLocaleDateString('he-IL', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    timeZone: 'Asia/Jerusalem',
  });
}

export function addDays(day: string, n: number) {
  const d = new Date(`${day}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

/** `count` dates starting at `start`, one every `stepDays` days (a weekly course = 7). */
export function weeklyDates(start: string, count: number, stepDays = 7) {
  return Array.from({ length: count }, (_, i) => addDays(start, i * stepDays));
}
