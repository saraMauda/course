# קובץ 2 – המקורות של המומחיות
# שלושה מקורות עצמאיים. כל אחד "איטי" (LATENCY) כמו קריאת API אמיתית,
# כדי שבכיתה רואים בעיניים: סדרתי לוקח ×3, במקביל לוקח ×1.

import json
import re
import time

LATENCY = 0.4  # שניות לכל מקור. סימולציית API

ACCOUNTS = {
    "312": {"customer": "312", "note": "שני חיובים זהים של 39.90 באותו חודש על חבילת גלישה."},
    "100": {"customer": "100", "note": "חיוב אחד תקין של 39.90 ביולי. אין כפל."},
}

KNOWLEDGE = [
    {"id": "double-charge", "text": "חיוב כפול: שני חיובים זהים באותו חודש על אותה חבילה. זכאות להחזר של חיוב אחד תוך 5 ימי עסקים, אחרי אימות."},
    {"id": "refund", "text": "החזר: רק אחרי אימות החיוב. לא מבטיחים סכום שלא מופיע בפירוט."},
    {"id": "cancel", "text": "ביטול מנוי: ההודעה בכתב או באפליקציה, והמנוי מסתיים בסוף מחזור החיוב."},
]

WEB_URL = "https://example.com/billing-news"

_ACCOUNT_RE = re.compile(r"(?:לקוח|מנוי|חבר)\s*(?:מספר\s*)?(\d+)")


def extract_account_id(text: str) -> str | None:
    m = _ACCOUNT_RE.search(text or "")
    return m.group(1) if m else None


def _words(text: str, fuzzy: bool = False) -> set:
    words = {w for w in re.findall(r"\w+", text) if len(w) > 2}
    if fuzzy:  # סבב מורחב: מורידות אות יחס בתחילת מילה (להחזר ~ החזר, החיוב ~ חיוב)
        words |= {w[1:] for w in words if len(w) > 3 and w[0] in "הלבכמו"}
    return words


def kb_search(question: str, top_k: int, fuzzy: bool = False) -> list[dict]:
    """חיפוש מילות מפתח. בכל סבב top_k גדל, ומסבב שני גם התאמה גמישה (הרחבת חיפוש)."""
    time.sleep(LATENCY)
    words = _words(question, fuzzy)
    scored = [(len(words & _words(item["text"], fuzzy)), item) for item in KNOWLEDGE]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for score, item in scored[:top_k] if score > 0]


def lookup_account(account_id: str) -> dict | None:
    time.sleep(LATENCY)
    return ACCOUNTS.get(account_id)


def web_search(question: str) -> str:
    """stub. «חדשות» = שירות החיפוש נופל (כדי להראות תשובה חלקית). «עדכני» = תוצאה. אחרת: אין תוצאות."""
    time.sleep(LATENCY)
    if "חדשות" in question:
        raise TimeoutError("שירות החיפוש לא זמין")
    if "עדכני" in question:
        return f"[stub] {WEB_URL} — עדכון: אין שינוי במדיניות החיוב החודש."
    return ""


def dumps(data) -> str:
    return json.dumps(data, ensure_ascii=False)
