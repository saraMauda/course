# tools/scrape.py – שליפת תוכן של דף
# הכלל החשוב: חותכים לפני שהמודל רואה. דף שלם בהיסטוריה = Context Rot.

import os
import re

from langchain.tools import tool

MAX_SCRAPE_CHARS = 600

_STUB_PAGES = {
    "https://example.com/billing-news": "עדכון: אין שינוי במדיניות החיוב החודש. " * 30,
}


@tool
def scrape_url(url: str) -> str:
    """שולף את תוכן הדף בכתובת נתונה (אחרי web_search). מחזיר רק את תחילת הדף."""
    if os.getenv("WEB_MODE", "").strip().lower() == "real":
        import httpx

        html = httpx.get(url, timeout=20.0, follow_redirects=True).text
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()
    else:
        text = _STUB_PAGES.get(url.strip(), "")
    if not text:
        return "הדף לא נמצא."
    if len(text) > MAX_SCRAPE_CHARS:
        return f"{text[:MAX_SCRAPE_CHARS]} [נחתך: {MAX_SCRAPE_CHARS} תווים מתוך {len(text)}]"
    return text
