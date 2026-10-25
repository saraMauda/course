---
title: "ניהול זיכרון וחיפוש חיצוני בזמן אמת"
description: "סגירה לפני פרויקט 2"
kind: "lesson"
lesson: "10"
division: 2
schedule: ["פתיחה 10'","תאוריה 20'","Lab Memory+Search 45'","תרגול 15'","סיכום 10'"]
hasHomework: "yes"
github: "https://github.com/saraMauda/course/tree/main/lessons/10-memory-web-search.md"
---

## 🌟 הקדמה

סוכן בלי זיכרון = כל הודעה "פעם ראשונה".  
סוכן עם זיכרון **לא** מנוהל = Context Rot.

בשיעור: **Checkpointers**, Trim/Summarize, וחיבור מנועי **חיפוש + סריקת דפים** למחקר בזמן אמת.

---

## 🧠 זיכרון שיחה ו-State

### Checkpointer (למשל `InMemorySaver`)
שומר state בין צעדים / בין הודעות תחת `thread_id`:

```text
create_agent(..., checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "user-42"}}
```

| סוג | שימוש |
|-----|--------|
| InMemory | lab, dev |
| SQLite / Postgres | production, sessions ארוכים |

בלי thread_id – אין "שיחה" אמיתית בין קריאות.

---

## ♻️ Context Rot: Trim / Summarize

כשההיסטוריה מתנפחת:

| מנגנון | מה עושה |
|--------|---------|
| **Trim** | חותך הודעות ישנות / tool results ישנים |
| **Summarize (middleware)** | מסכם מקטע ישן לתמצית, שומר רציפות |
| **Skills במקום MCP כבד** | פחות metadata קבוע בקונטקסט |
| **דחיסת tool outputs** | לא לשמור HTML גולמי שלם |

מהסיכום: לקראת גבול החלון – compression (למשל מחיקת tool calls ישנים).

---

## 🌐 חיפוש חיצוני בזמן אמת

### מה מנוע/סורק נותן?

| פעולה | משמעות |
|-------|--------|
| **search** | תוצאות חיפוש (כותרות, קישורים, snippets) |
| **scrape** | תוכן מדף ספציפי |
| **map / crawl** | מיפוי / סריקת אתר (כלים מתקדמים) |

### Tavily / Firecrawl
- **Tavily** – חיפוש מותאם לסוכנים  
- **Firecrawl** – scrape/crawl חזק; בסיכום האישי: *שימוש ב-Firecrawl כי Tavily חסום (NetFree)*  

בחרו לפי זמינות רשת אצלכם.

```python
@tool
def web_search(query: str) -> str:
    """חיפוש מידע עדכני באינטרנט."""
    ...

@tool
def scrape_url(url: str) -> str:
    """שליפת תוכן עיקרי מדף."""
    ...
```

האייג'נט מחליט **מתי** לחפש ומתי לגרד – לפי ReAct.

---

## 📐 פלט מובנה + Hooks (מה-ADVANCED)

- `init_chat_model` / `ChatGoogleGenerativeAI`
- Pydantic: `ResearchAnswer` לפלט מובנה
- middleware לסיכום הקשר
- UI: Streamlit

```python
class ResearchAnswer(BaseModel):
    summary: str
    sources: list[str]
    confidence: float
```

---

## 🛠️ Lab: Mini Research Agent

### שלב 1
Agent + checkpointer + thread_id – שאלו שאלה המשכית ("מה אמרתי קודם?").

### שלב 2
הוסיפו `web_search` – שאלה עדכנית ("כמה סוכני AI …?").

### שלב 3
הוסיפו `scrape_url` אחרי search.

### שלב 4
middleware/summarize אחרי N הודעות – השוו אורך קונטקסט.

### שלב 5
query rewrite: skill או tool שמנסח מחדש שאילתה גרועה.

---

## 🧩 תכולה

- Memory + Checkpointers
- Trim / Summarize מול Context Rot
- Tavily / Firecrawl
- פלט מחקר מובנה

---

## 💡 טיפים ו-Gotchas

- אל תחזירו scrape מלא (HTML ענק) למודל – חתכו.
- search בלי rewrite = שאילתות חלשות.
- זיכרון ≠ אמת; שמרו מקורות לצד מסקנות.
- Rate limits ו-API keys בסוד (.env).

---

## ✅ לסיכום

- Checkpointer = זיכרון שיחה מנוהל.
- Trim/Summarize = חיסון ל-Context Rot.
- חיפוש + scrape = מחקר חי.
- יש לכם את כל רכיבי **פרויקט 2**.

---

## 👩‍💻 קוד / קישורים

- דמו הכיתה: [`demos/10-memory-search`](https://github.com/saraMauda/course/tree/main/demos/10-memory-search/README.md)

---

## 🏠 תרגיל בית

1. **שיעורי בית 10** – אותו דמו, על ספריות עירוניות, עם מדידת שלושת מצבי הזיכרון: [10-שיעורי-בית.md](10-שיעורי-בית.md).
2. **התקדמות בפרויקט 2:** השלימו Research Agent מינימלי: search + scrape + memory + לפחות MCP אחד (או mock מתועד).  
   עברו למפרט הפרויקט.

---

## 📎 מקורות

- `ADVANCED LANGCHAIN - סיכום אישי`
- `Lang chain סיכום אישי`
