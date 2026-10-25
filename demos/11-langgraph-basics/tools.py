# קובץ 2 – הכלים
# אותם כלים משיעור 09, בלי שינוי. ההבדל: כאן אנחנו מריצות אותם בעצמנו ב-tools node,
# ולא `create_agent`.

import json
import re

from langchain.tools import tool

ACCOUNTS = {
    "312": {"customer": "312", "note": "שני חיובים זהים של 39.90 באותו חודש על חבילת גלישה."},
    "100": {"customer": "100", "note": "חיוב אחד תקין של 39.90 ביולי. אין כפל."},
}

KNOWLEDGE = [
    {"id": "double-charge", "text": "חיוב כפול: שני חיובים זהים באותו חודש על אותה חבילה. זכאות להחזר של חיוב אחד תוך 5 ימי עסקים, אחרי אימות."},
    {"id": "refund", "text": "החזר: רק אחרי אימות החיוב. לא מבטיחים סכום שלא מופיע בפירוט."},
    {"id": "cancel", "text": "ביטול מנוי: ההודעה בכתב או באפליקציה, והמנוי מסתיים בסוף מחזור החיוב."},
]


@tool
def get_account(customer_id: str) -> str:
    """מחזיר את פירוט החשבון והחיובים לפי מספר לקוח. השתמשי כשהלקוחה שואלת על חיוב ויש מספר לקוח."""
    key = customer_id.strip()
    data = ACCOUNTS.get(key, {"customer": key, "note": "הלקוח לא במאגר."})
    return json.dumps(data, ensure_ascii=False)


@tool
def search_sources(query: str) -> str:
    """חיפוש במאגר הידע של החברה: מדיניות, החזרים וביטולים. השתמשי כשצריך לדעת מה הנוהל. לא למידע על לקוחה מסוימת."""

    def words_of(text: str) -> set:
        return {w for w in re.findall(r"\w+", text) if len(w) > 2}

    words = words_of(query)
    scored = [(len(words & words_of(item["text"])), item) for item in KNOWLEDGE]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    best = [item for score, item in scored[:2] if score > 0]
    if not best:
        return "לא נמצא במאגר."
    return " ".join(f"[{item['id']}] {item['text']}" for item in best)


TOOLS = [get_account, search_sources]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}
