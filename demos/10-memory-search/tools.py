# קובץ 2 – כלי המחקר
# web_search ו-scrape_url. בדמו אין רשת: התוצאות קבועות (stub), כדי שהכל ירוץ בכיתה.
# בפרויקט 2 מחליפים ב-Tavily / Firecrawl (Firecrawl אם Tavily חסום).
# הכלל החשוב כאן: scrape_url **חותך** את הדף לפני שהמודל רואה אותו.

from langchain.tools import tool

MAX_SCRAPE_CHARS = 400  # בלי חיתוך, דף אחד שווה אלפי טוקנים בהיסטוריה לכל ההמשך (Context Rot)

RESULTS = [
    {"title": "מדריך: סוכני AI ב-2026", "url": "https://example.com/ai-agents-2026",
     "snippet": "סקירה של יותר מ-40 מסגרות לבניית סוכנים."},
    {"title": "השוואה: LangChain מול LangGraph", "url": "https://example.com/langchain-vs-langgraph",
     "snippet": "מתי עוטפים בלולאה מוכנה, ומתי בונים גרף."},
    {"title": "מהו Agent Harness", "url": "https://example.com/agent-harness",
     "snippet": "הכול חוץ מהמודל: לולאה, כלים, הקשר, בקרה."},
]

_BODY = (
    "סוכן הוא מודל שמנהל לולאה של חשיבה, פעולה ותצפית. "
    "המסגרות הנפוצות כוללות LangChain, LangGraph, LlamaIndex ועוד עשרות אחרות. "
)
PAGES = {r["url"]: f"{r['title']}. " + _BODY * 12 for r in RESULTS}


@tool
def web_search(query: str) -> str:
    """חיפוש מידע עדכני באינטרנט. מחזיר כותרות, כתובות ותקצירים. השתמשי כשצריך עובדה על העולם ואין לך מקור."""
    lines = [f"{i}. {r['title']} — {r['url']} — {r['snippet']}" for i, r in enumerate(RESULTS, 1)]
    return "\n".join(lines)


@tool
def scrape_url(url: str) -> str:
    """שולף את תוכן הדף בכתובת נתונה (אחרי web_search). מחזיר רק את תחילת הדף. השתמשי כשצריך פרטים מדף מסוים."""
    text = PAGES.get(url.strip())
    if text is None:
        return "הדף לא נמצא."
    if len(text) > MAX_SCRAPE_CHARS:
        return f"{text[:MAX_SCRAPE_CHARS]} [נחתך: {MAX_SCRAPE_CHARS} תווים מתוך {len(text)}]"
    return text


TOOLS = [web_search, scrape_url]
