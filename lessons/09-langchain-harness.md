# 09 | 💬 פיתוח ב-LangChain – Harness, Tools ו-ReAct

> **מבנה מפגש:** פתיחה 10' · תאוריה 20' · Live coding Agent+Tools 45' · תרגול 15' · סיכום 10'  
> **חטיבה 2** · מצטבר ל-**פרויקט 2**

---

## 🌟 הקדמה

LangChain נולדה כדי **לפתור את כאב בניית ה-Agents**: לולאות, כלים, זיכרון, חיבור למודלים – במקום לכתוב הכל מאפס.

> **Agent = Model + Harness**

ה-**Harness** (מונח קנוני מ-LangChain / Vivek ושות') הוא כל מה **שאינו** המודל:

- לולאת סנכרון (ReAct loop)
- ממשק כלים
- ניהול הקשר
- מנגנוני בקרה

סוגי harness נפוצים (מהסיכום): מערכת קבצים, git, CLI+sandbox, כלי חיפוש, MCP.

---

## 🆕 LangChain באקוסיסטם

| רכיב | תפקיד |
|------|--------|
| **LangChain** | בניית agents, tools, מודלים |
| **LangGraph** | גרפים, state machines, בקרה עמוקה (שיעורים 11+) |
| **LangSmith** | Tracing, evaluation, production (שיעור 14) |

**שימו לב:** הספרייה מתעדכנת במהירות – להיעזר ב-docs עדכניים / Context7.

`init_chat_model` – מחליפים ספק מודל בקלות; חיסרון: יכולות לא זהות בין ספקים.

---

## 🛠️ Tools מותאמים – `@tool`

```python
from langchain.tools import tool

@tool
def search_sources(query: str) -> str:
    """חיפוש סמנטי במאגר הידע הפנימי. השתמש כשצריך מידע מה-KB."""
    # כאן: embedding + שליפת cosine / VectorStore מפרויקט 1
    return retrieved_context
```

עטיפת **RAG כ-Tool** הופכת את בוט התמיכה לחלק מארגז הכלים של סוכן רחב יותר.

---

## 🔁 לולאת ReAct ב-LangChain

`create_agent` (או המקבילה בגרסה שלכם) עוטף:

```text
שאלה → מודל → tool_calls? 
           כן → הרצת tools → observation → חזרה למודל
           לא → תשובה סופית
```

טיפול בשגיאות הרצה:

- tool timeout / exception → הודעת שגיאה **כ-observation**, לא קריסת תהליך
- max iterations – מניעת לולאות אינסוף
- validation על args (Pydantic)

---

## 🖼️ דוגמאות מהסיכום האישי

### Agent 1 – שאלות על Repo
- `create_agent` + מודל (למשל ChatGoogleGenerativeAI)
- `MultiServerMCPClient` + GitHub token
- לולאת UI: `while True` לשאלות מרובות

### Agent 2 – "מורה ל-Repo" + Memory
- `InMemorySaver` / checkpointer
- System prompt ייעודי
- `thread_id` / session כדי לזכור הקשר

### Deep agents / GitHub mentor
- שאלה כמו "מתי העדכון האחרון?" → tool → סידור תשובה

---

## 🛠️ Lab

### שלב 1
Agent עם tool אחד (`get_time` / `calculator`) – לראות tool_call.

### שלב 2
הוסיפו `search_sources` (RAG מפרויקט 1 או mock).

### שלב 3
חברו MCP tool list (משיעור 7) לתוך אותו agent.

### שלב 4
הוסיפו טיפול בשגיאה מכוונת (tool זורק) – ודאו שהמודל ממשיך.

---

## 🧩 תכולה

- נוסחת Harness
- `@tool` וכלי מותאם
- RAG כ-tool דינמי
- ReAct ב-LangChain
- טיפול בשגיאות

---

## 💡 טיפים ו-Gotchas

- תיאור ה-tool = פרומפט – השקיעו בו.
- יותר מדי tools → מודל מתבלבל (כמו MCP).
- UI: Streamlit/Gradio מעל הלולאה (לפי העדפה).
- Firecrawl vs Tavily – לפי זמינות רשת (ראו שיעור 10).

---

## ✅ לסיכום

- Agent אמיתי = מודל + הנדסת ריצה (Harness).
- LangChain מקצרת את הדרך ל-Tools + ReAct.
- RAG הופך לכלי אחד מתוך ארגז, לא "המערכת כולה".
- זיכרון וחיפוש חיצוני – בשיעור הבא.

---

## 👩‍💻 קוד / קישורים

- דמו הכיתה: [`demos/09-langchain-harness`](../demos/09-langchain-harness/README.md)

- https://www.langchain.com/blog/the-anatomy-of-an-agent-harness  
- https://docs.langchain.com/oss/python/langchain/overview  
- `Lang chain סיכום אישי`, `18 LangChain - Project`

---

## 🏠 תרגיל בית

1. **שיעורי בית 09** – אותו דמו, על ספרייה עירונית, עם System prompt שכתוב על ידכן: [09-שיעורי-בית.md](09-שיעורי-בית.md).
2. **התקדמות בפרויקט 2:**

   1. ממשו Agent עם לפחות 2 tools: `web_search` (stub מותר) + `search_sources`.  
   2. הוסיפו system prompt: מתי להשתמש בכל כלי.  
   3. תעדו 3 ריצות: tool נכון, tool שגוי שתוקן, כישלון tool.

---

## 📎 מקורות

- ADVANCED LANGCHAIN – בהמשך בשיעור 10  
- Anthropic Effective Agents – שיעור 8
