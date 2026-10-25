# קובץ 3 – הכלי החיצוני
# web_search הוא stub: בדמו אין רשת. בפרויקט מחליפים ב-Tavily או Firecrawl.
# בגרף הוא נחשף למודל רק כשהמשתמשת הפעילה «הרחבה לאינטרנט».

from langchain.tools import tool


@tool
def web_search(query: str) -> str:
    """חיפוש באינטרנט. השתמשי רק כשהמקורות שאושרו לא עונים על השאלה."""
    return f"[stub] אין חיבור לרשת בדמו. כאן היו מופיעות תוצאות חיפוש עבור: {query}"


TOOLS = [web_search]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}
