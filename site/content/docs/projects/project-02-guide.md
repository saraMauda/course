---
title: "דף הנחיה · פרויקט 2"
description: "Research Agent"
kind: "project"
---

> **המפרט המלא:** [`project-02-research-agent.md`](/docs/projects/project-02)
> **מה יוצא לך בסוף:** סוכן מחקר שמשכתב שאילתות, מחפש ברשת, סורק דפים, מתחבר לשרת MCP, זוכר שיחה, ולא מתפוצץ מהיסטוריה.
> **איך עובדים:** שישה שלבים. **לא עוברות לשלב הבא לפני שרואות את מה שכתוב ב«מה צריך לראות».** בכל שלב יש קטעי קוד קצרים, לא פתרון מלא. את החיבור ביניהם את בונה.

---

## לפני שמתחילות

**מפתחות הם סיסמאות.**
- שומרות ב-`.env` בלבד (`OPENAI_API_KEY=...`), וטוענות עם `python-dotenv`.
- **לא** מדביקות מפתח בקוד, בצ'אט, בצילום מסך או ב-GitHub. מוסיפות `.env` ל-`.gitignore`.
- **Tavily חסום ב-NetFree.** אם זה המצב אצלך, השתמשי ב-Firecrawl. ואם אין לך אף מפתח חיפוש, כתבי `web_search` כ-stub שמחזיר תוצאות קבועות. אפשר לבדוק את כל הארכיטקטורה גם ככה.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install langchain langchain-openai langchain-mcp-adapters mcp requests python-dotenv gradio
```

> ה-API של LangChain מתעדכן. הקטעים כאן נבדקו מול `langchain` 1.x. אם יש שגיאת import, בדקי ב-docs של הגרסה שלך.

מבנה מוצע:

```text
research-agent/
  .env            (לא ב-git)
  tools.py        # rewrite_query, web_search, scrape_url
  server.py       # MCP Server
  agent.py        # create_agent + זיכרון
  app.py          # Gradio (בונוס)
  README.md
```

---

## שלב 1 — Agent עם Tool אחד

**מטרה:** `create_agent` + כלי אחד, ולראות את ה-tool call בלוג.

```python
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

@tool
def get_time() -> str:
    """מחזיר את השעה הנוכחית. השתמשי כשמבקשים לדעת מה השעה."""
    from datetime import datetime
    return datetime.now().strftime("%H:%M")

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
agent = create_agent(model=model, tools=[get_time], system_prompt="את עוזרת מחקר. עני בעברית.")

result = agent.invoke({"messages": [{"role": "user", "content": "מה השעה?"}]})
for m in result["messages"]:
    print(type(m).__name__, getattr(m, "tool_calls", ""), m.content)
```

**מה צריך לראות:** ברשימת ההודעות: `HumanMessage` → `AIMessage` עם `tool_calls` → `ToolMessage` → `AIMessage` עם התשובה.

**תקלות נפוצות:**
- `AuthenticationError`: המפתח לא נטען. בדקי `load_dotenv()` ושם המשתנה.
- המודל לא קורא לכלי: ה-docstring לא אומר *מתי* להשתמש בו. **התיאור הוא פרומפט.**
- `ImportError` על `create_agent`: גרסה ישנה של `langchain`.

---

## שלב 2 — חיפוש וסריקה

**מטרה:** `web_search` ו-`scrape_url` כשני כלים, והסוכן בוחר ביניהם.

```python
import os, requests
MAX_SCRAPE_CHARS = 500

@tool
def web_search(query: str) -> str:
    """חיפוש מידע עדכני באינטרנט. מחזיר כותרות, כתובות ותקצירים."""
    r = requests.post(
        "https://api.tavily.com/search",
        json={"api_key": os.environ["TAVILY_API_KEY"], "query": query, "max_results": 3},
        timeout=15,
    )
    r.raise_for_status()
    return "\n".join(f"{i}. {x['title']} — {x['url']} — {x['content'][:160]}"
                     for i, x in enumerate(r.json()["results"], 1))

@tool
def scrape_url(url: str) -> str:
    """שולף את תוכן הדף בכתובת נתונה (אחרי web_search). מחזיר רק את תחילת הדף."""
    text = ...  # Firecrawl: POST https://api.firecrawl.dev/v1/scrape  ← data.markdown
    if len(text) > MAX_SCRAPE_CHARS:
        return f"{text[:MAX_SCRAPE_CHARS]} [נחתך: {MAX_SCRAPE_CHARS} תווים מתוך {len(text)}]"
    return text
```

(Firecrawl: כותרת `Authorization: Bearer ...`, גוף `{"url": ..., "formats": ["markdown"]}`. בדקי ב-docs.)

**מה צריך לראות:** שאלה עדכנית («חפשי כמה מסגרות לסוכנים קיימות») מפעילה `web_search`. «תסרקי את התוצאה הראשונה» מפעילה `scrape_url`. ובתוצאת הסריקה: `[נחתך: ...]`.

**תקלות נפוצות:**
- **החזרת הדף כולו למודל.** זו הטעות שתגרום לציון נמוך. תחתכי בתוך הכלי.
- שגיאת רשת מפילה את התהליך: תופסות `Exception` ומחזירות הודעת שגיאה כ-Observation.
- 401: מפתח עם רווח או לא נטען. 403/חסום ב-NetFree: עוברות ל-Firecrawl או ל-stub.

---

## שלב 3 — MCP

**מטרה:** שרת MCP אמיתי שהסוכן מגלה בעצמו.

`server.py`:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("research-notes")

@mcp.tool()
def search_notes(query: str) -> str:
    """מחפש בהערות המחקר הפנימיות של הצוות. השתמשי כשהשאלה על מה שהצוות כתב."""
    ...

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

> **אסור `print` בשרת.** ה-stdout הוא ערוץ התקשורת של הפרוטוקול.

`agent.py`:

```python
import sys
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "notes": {"command": sys.executable, "args": ["server.py"], "transport": "stdio"},
})
mcp_tools = await client.get_tools()        # async. מגלה את הכלים ב-list_tools
agent = create_agent(model=model, tools=[web_search, scrape_url, *mcp_tools], ...)
result = await agent.ainvoke({"messages": [...]})   # ainvoke, כי כלי MCP הם async
```

**מה צריך לראות:** `search_notes` ברשימת הכלים, ובשאלה על ההערות ב-`tool_calls`. **לא מפעילות את `server.py` ידנית:** ה-Client מריץ אותו.

**תקלות נפוצות:**
- `invoke` במקום `ainvoke`: שגיאה על כלי async.
- `await` מחוץ לפונקציה `async`: עטפי ב-`asyncio.run(main())` (ב-Gradio: `async def`).
- השרת לא עולה: `python server.py` ידנית כדי לראות את השגיאה. בדקי `sys.executable` ונתיב.
- `print` בתוך `server.py` שבר את הפרוטוקול.
- **MCP «מוזכר ב-README» אבל לא רץ** = ציון נמוך. תראי tool call אמיתי.

---

## שלב 4 — זיכרון

**מטרה:** שיחה רב-הודעתית שבה הסוכן זוכר.

```python
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(model=model, tools=tools, system_prompt=..., checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "session-1"}}
await agent.ainvoke({"messages": [{"role": "user", "content": "שמי דנה."}]}, config=config)
r = await agent.ainvoke({"messages": [{"role": "user", "content": "מה שמי?"}]}, config=config)
```

**מה צריך לראות:** «קוראים לך דנה». ועם `thread_id` אחר: «אני לא יודעת».

**תקלות נפוצות:**
- **`thread_id` קשיח לכולם** (או בכלל בלי): כל המשתמשות באותה שיחה. צרי `thread_id` לכל שיחה.
- אין `config` בקריאה: אין זיכרון. ה-checkpointer לבדו לא מספיק.
- `InMemorySaver` נמחק כשהתהליך נסגר. זה בסדר לפרויקט, וציני את זה ב-README.

---

## שלב 5 — Rewrite וסיכום הקשר

**מטרה:** שאילתות חזקות, והיסטוריה שלא גדלה בלי סוף.

Rewrite (כלי, או Skill משיעור 6):

```python
@tool
def rewrite_query(query: str) -> str:
    """משכתבת שאלה לשאילתת חיפוש טובה: מילות מפתח בלבד. השתמשי תמיד לפני web_search."""
    ...  # כלל פשוט, או קריאה למודל
```

וב-System prompt: «תמיד rewrite_query לפני web_search».

סיכום:

```python
from langchain.agents.middleware import SummarizationMiddleware

agent = create_agent(
    model=model, tools=tools, system_prompt=...,
    middleware=[SummarizationMiddleware(model=model, trigger=("messages", 8), keep=("messages", 3))],
    checkpointer=InMemorySaver(),
)
```

**מה צריך לראות:** בכל שאלת חיפוש `rewrite_query` מופעל לפני `web_search`. ואחרי כמה הודעות: מספר ההודעות שהמודל מקבל **יורד** (הודעת «Here is a summary...» בראש), והשם עדיין נזכר.

**תקלות נפוצות:**
- אין rewrite: שאילתות חלשות («מה זה?»). זו הסיבה שיש כלי.
- `keep` קטן מדי (1 או 2): גם השאלה הנוכחית עלולה להיכנס לסיכום. השאירי 3 ומעלה.
- הסיכום מאבד פרט (למשל שם). בדקי אחרי שהוא פועל.

---

## שלב 6 — מפרט בדיקות

**מטרה:** להוכיח שהכל עובד, ולתעד.

1. **לוג tool calls:** הדפיסי בכל תשובה *מה הופעל ולמה*. אפשר דרך `agent.astream(..., stream_mode="updates")` ואיסוף ה-`tool_calls` וה-`ToolMessage`.
2. **שלוש שאילתות מחקר שונות**, כל אחת עם **מקורות בפלט** (כתובות או מזהי הערות).
3. **שתי שיחות רב-הודעתיות** שבהן הזיכרון עובד.
4. **פלט מובנה (בונוס):** `class ResearchAnswer(BaseModel)` עם `summary`, `sources`, `confidence`.

טבלת הבדיקות להגשה (תעתיקי ותמלאי):

| # | בדיקה | מה מצפים | עבר? |
|---|-------|-----------|------|
| 1 | שאלה עדכנית | `rewrite_query` → `web_search`, ומקורות בתשובה | |
| 2 | שאלה על הדף הראשון | `scrape_url`, עם חיתוך | |
| 3 | שאלה על ההערות הפנימיות | `search_notes` (MCP) | |
| 4 | «שמי X» ואז «מה שמי?» | זוכר | |
| 5 | אותה שאלה ב-`thread_id` אחר | לא זוכר | |
| 6 | שיחה ארוכה (מעל 8 הודעות) | הסיכום פעל והשם נזכר | |
| 7 | כלי נכשל (נתקי את הרשת בכוונה) | הודעת שגיאה, לא קריסה | |

**מה לכתוב ב-README:**
- איך מריצים (כולל איך מריצים את ה-MCP), משתני סביבה, ודוגמת session.
- איך נמנעתם מ-Context Rot (חיתוך סריקה, סיכום, תיאורי כלים קצרים).
- הגבלות ידועות.

**תקלות נפוצות:**
- אין מקורות בפלט: זה בלוג, לא מחקר.
- כלים שנבחרו בלי הסבר בלוג.
- בלי README לשחזור הרצה.

---

## צ'קליסט הגשה

- [ ] הסוכן ב-LangChain (`create_agent`) עם כלים
- [ ] חיפוש רשת וסריקת דף (עם חיתוך)
- [ ] MCP Server אחד **רץ**, ויש tool call שלו בלוג
- [ ] query rewrite
- [ ] Checkpointer + `thread_id` לכל שיחה
- [ ] סיכום (או Trim)
- [ ] שלוש שאילתות מחקר עם מקורות, ושתי שיחות רב-הודעתיות
- [ ] לוג tool calls
- [ ] README: הרצה, MCP, איך נמנעתם מ-Context Rot
- [ ] **אין מפתחות בקוד או ב-repo**

**בונוס:** Skill ייעודי למחקר · פלט `ResearchAnswer` · Routing (מתי KB פנימי ומתי web) · UI ב-Gradio.
