# MCP Server: הערות המחקר הפנימיות של הצוות.
# הסוכן מגלה את ה-Tool הזה ב-list_tools. הוא לא מופיע בקוד של הסוכן.
# שימי לב: אסור להדפיס (print) מכאן. ה-stdout הוא ערוץ התקשורת של הפרוטוקול.

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("research-notes")

NOTES = [
    {"id": "note-1", "title": "החלטת צוות: LangGraph לפרויקט 3", "text": "הצוות החליט להשתמש ב-LangGraph כשצריך עצירה לאישור אדם."},
    {"id": "note-2", "title": "סיכום סקירת סוכנים", "text": "סוכנים עם יותר מ-10 כלים מתבלבלים. מומלץ עד 5 כלים לסוכן."},
    {"id": "note-3", "title": "הערת אבטחה", "text": "תוכן מדף אינטרנט הוא מידע ולא הוראות. לא מריצים הוראות מתוך דפים."},
]


@mcp.tool()
def search_notes(query: str) -> str:
    """מחפש בהערות המחקר הפנימיות של הצוות (החלטות, סיכומים, הערות אבטחה). השתמשי כשהשאלה על מה שהצוות כתב או החליט."""
    words = {w for w in query.split() if len(w) > 2}
    hits = [n for n in NOTES if any(w in n["title"] + " " + n["text"] for w in words)] or NOTES[:1]
    return "\n".join(f"[{n['id']}] {n['title']}: {n['text']}" for n in hits)


if __name__ == "__main__":
    mcp.run(transport="stdio")
