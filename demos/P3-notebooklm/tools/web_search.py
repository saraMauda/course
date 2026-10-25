# tools/web_search.py – חיפוש חיצוני
# בלי מפתח: stub, כדי שהכל ירוץ בכיתה בלי רשת.
# עם TAVILY_API_KEY ו-WEB_MODE=real: Tavily אמיתי. (אם Tavily חסום אצלכן, החליפו ב-Firecrawl.)

import os

from langchain.tools import tool

WEB_URL = "https://example.com/billing-news"


def _real() -> bool:
    return os.getenv("WEB_MODE", "").strip().lower() == "real" and bool(os.getenv("TAVILY_API_KEY"))


@tool
def web_search(query: str) -> str:
    """חיפוש באינטרנט. השתמשי רק כשהמקורות שאושרו לא עונים על השאלה. התוצאה היא מהרשת, לא מהמקורות."""
    if not _real():
        return f"[stub] {WEB_URL} — אין חיבור לרשת בדמו. כאן היו מופיעות תוצאות חיפוש עבור: {query}"
    import httpx

    resp = httpx.post(
        "https://api.tavily.com/search",
        json={"api_key": os.environ["TAVILY_API_KEY"], "query": query, "max_results": 3},
        timeout=20.0,
    )
    resp.raise_for_status()
    rows = resp.json().get("results", [])
    return "\n".join(f"{r.get('title', '')} — {r.get('url', '')} — {str(r.get('content', ''))[:200]}" for r in rows) or "אין תוצאות."
