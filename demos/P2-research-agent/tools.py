# כלי המחקר: web_search, scrape_url, rewrite_query.
# web_search: Tavily אם יש TAVILY_API_KEY, אחרת Firecrawl אם יש FIRECRAWL_API_KEY, אחרת stub (בלי רשת).
# הערה: Tavily חסום ב-NetFree, ולכן יש Firecrawl. מפתחות רק ב-.env, אף פעם לא בקוד או בצ'אט.
# scrape_url חותך את הדף לפני שהמודל רואה אותו (Context Rot).

import os
import re

import requests
from langchain.tools import tool

MAX_SCRAPE_CHARS = 500
TIMEOUT = 15

_STOP = {"מה", "האם", "תגידי", "אפשר", "לי", "על", "של", "את", "זה", "כמה", "איך", "למה", "היום", "בבקשה"}

# stub: תוצאות קבועות כשאין מפתחות (כדי שהכל ירוץ גם בלי רשת)
_STUB_RESULTS = [
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
_STUB_PAGES = {r["url"]: f"{r['title']}. " + _BODY * 12 for r in _STUB_RESULTS}


def provider() -> str:
    if os.getenv("TAVILY_API_KEY"):
        return "tavily"
    if os.getenv("FIRECRAWL_API_KEY"):
        return "firecrawl"
    return "stub"


def _format(results: list[dict]) -> str:
    return "\n".join(f"{i}. {r['title']} — {r['url']} — {r.get('snippet', '')}" for i, r in enumerate(results, 1))


@tool
def rewrite_query(query: str) -> str:
    """משכתבת שאלה לשאילתת חיפוש טובה: מילות מפתח בלבד, בלי מילות שאלה. השתמשי תמיד לפני web_search."""
    words = [w for w in re.findall(r"[\w\-]+", query) if w not in _STOP and len(w) > 1]
    return " ".join(dict.fromkeys(words)) or query


@tool
def web_search(query: str) -> str:
    """חיפוש מידע עדכני באינטרנט. מחזיר כותרות, כתובות ותקצירים. השתמשי אחרי rewrite_query, כשצריך עובדה על העולם."""
    kind = provider()
    try:
        if kind == "tavily":
            r = requests.post(
                "https://api.tavily.com/search",
                json={"api_key": os.environ["TAVILY_API_KEY"], "query": query, "max_results": 3},
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            return _format([{"title": x["title"], "url": x["url"], "snippet": x.get("content", "")[:160]} for x in r.json()["results"]])
        if kind == "firecrawl":
            r = requests.post(
                "https://api.firecrawl.dev/v1/search",
                headers={"Authorization": f"Bearer {os.environ['FIRECRAWL_API_KEY']}"},
                json={"query": query, "limit": 3},
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            return _format([{"title": x.get("title", ""), "url": x["url"], "snippet": x.get("description", "")[:160]} for x in r.json()["data"]])
    except Exception as exc:  # כלי שנכשל חוזר כ-Observation, לא קריסה
        return f"שגיאת חיפוש ({kind}): {exc}"
    return _format(_STUB_RESULTS)


@tool
def scrape_url(url: str) -> str:
    """שולף את תוכן הדף בכתובת נתונה (אחרי web_search). מחזיר רק את תחילת הדף. השתמשי כשצריך פרטים מדף מסוים."""
    kind = provider()
    text = None
    try:
        if kind == "firecrawl":
            r = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={"Authorization": f"Bearer {os.environ['FIRECRAWL_API_KEY']}"},
                json={"url": url, "formats": ["markdown"]},
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            text = r.json()["data"]["markdown"]
        elif kind == "tavily":
            r = requests.post(
                "https://api.tavily.com/extract",
                json={"api_key": os.environ["TAVILY_API_KEY"], "urls": [url]},
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            text = r.json()["results"][0]["raw_content"]
        else:
            text = _STUB_PAGES.get(url.strip())
    except Exception as exc:
        return f"שגיאת סריקה ({kind}): {exc}"
    if text is None:
        return "הדף לא נמצא."
    if len(text) > MAX_SCRAPE_CHARS:
        return f"{text[:MAX_SCRAPE_CHARS]} [נחתך: {MAX_SCRAPE_CHARS} תווים מתוך {len(text)}]"
    return text


LOCAL_TOOLS = [rewrite_query, web_search, scrape_url]
