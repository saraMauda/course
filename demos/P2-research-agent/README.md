# פתרון ייחוס | פרויקט 2 – Research Agent

סוכן מחקר אוטונומי שעומד בכל שבע דרישות החובה של [`projects/project-02-research-agent.md`](../../projects/project-02-research-agent.md), ובונוס: פלט מובנה (`ResearchAnswer`) ולוג tool calls.

> **זה פתרון ייחוס למרצה** (ולבדיקת מקרי הקצה). הסטודנטיות עובדות לפי [`דף ההנחיה`](../../projects/project-02-דף-הנחיה-לסטודנטים.md) ובונות בעצמן.

משפט עוגן:

> **rewrite → search → scrape → (MCP) → תשובה עם מקורות. זיכרון ≠ אמת, וכל דף נחתך לפני שהמודל רואה אותו.**

---

## ארכיטקטורה

```text
משתמשת
  → Gradio (app.py, async)
      → Research (agent.py)
          create_agent( model, tools, system_prompt, middleware, checkpointer )
            ├─ tools.py:   rewrite_query · web_search · scrape_url      (כלים מקומיים)
            ├─ server.py:  search_notes                                  (MCP Server, stdio)
            │              ← MultiServerMCPClient (langchain-mcp-adapters) מגלה אותו ב-list_tools
            ├─ SummarizationMiddleware  (trigger = 8 הודעות, keep = 3)
            ├─ record_context           (לוג: כמה הודעות המודל קיבל)
            └─ InMemorySaver + thread_id  (זיכרון שיחה)
      → ResearchAnswer(summary, sources, confidence) + לוג tool calls
```

| קובץ | תפקיד |
|------|-------|
| `agent.py` | `Research`: טוען MCP פעם אחת, בונה את הסוכן, `ask` עם `astream` ובניית `ResearchAnswer` ולוג |
| `tools.py` | שלושה כלים. `web_search`: Tavily → Firecrawl → stub. `scrape_url` חותך ל-500 תווים |
| `server.py` | שרת MCP אמיתי (FastMCP, stdio) עם `search_notes` על הערות צוות |
| `llm_client.py` | חיבור למודל (OpenAI / Gemini / הדגמה מקומית) |
| `app.py` | החלון: תשובה, `ResearchAnswer`, לוג tool calls, סטטוס MCP, שורת הקשר |
| `check.py` | בדיקת הצ'קליסט במצב מקומי: PASS/FAIL לכל סעיף |

---

## הרצה

```bash
cd demos/P2-research-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

או לחיצה כפולה על `הרצה.bat`.

בדיקה אוטומטית (בלי מפתחות ובלי אינטרנט):

```bash
python check.py
```

### משתני סביבה (`.env`)

| משתנה | מה עושה |
|-------|---------|
| `LLM_PROVIDER` | `auto` (ברירת מחדל), `gemini`, או `mock` להדגמה בלי אינטרנט |
| `OPENAI_API_KEY`, `GEMINI_API_KEY` | מודל. אם OpenAI חסום, עוברים ל-Gemini |
| `TAVILY_API_KEY` | חיפוש וסריקה דרך Tavily. **חסום ב-NetFree** |
| `FIRECRAWL_API_KEY` | חיפוש וסריקה דרך Firecrawl. הבחירה אם Tavily חסום |

בלי מפתח חיפוש: `web_search` ו-`scrape_url` עובדים כ-stub (תוצאות קבועות). **מפתחות רק ב-`.env`, לא בקוד ולא בצ'אט.**

### איך מריצים את ה-MCP

אין צורך להפעיל את `server.py` ידנית. `MultiServerMCPClient` מפעיל אותו כתהליך נפרד (stdio) בעצמו, וה-Host מגלה את `search_notes` ב-`list_tools`. בחלון, בשורת הסטטוס: «MCP פעיל: נטענו ['search_notes']». אם השרת לא עולה, הסוכן ממשיך בלי הכלי ואומר זאת (degrade).

> אסור `print` ב-`server.py`: ה-stdout הוא ערוץ הפרוטוקול.

---

## דוגמת שיחה (לחצי על הדוגמאות לפי הסדר)

| # | הודעה | מה קורה |
|---|-------|---------|
| 1 | שלום, שמי דנה. | בלי כלי. «נעים להכיר, דנה.» |
| 2 | חפשי מה מצב סוכני ה-AI היום | `rewrite_query` → `web_search` → `scrape_url`. תשובה עם 3 מקורות. `confidence` גבוה |
| 3 | מה כתבו בהערות הצוות על LangGraph? | `search_notes` (MCP). מקור: `note-1` |
| 4 | חפשי מה ההבדל בין LangChain ל-LangGraph | `rewrite_query` → `web_search` (בלי סריקה) |
| 5 | מה שמי? | «קוראים לך דנה», גם אחרי שהסיכום פעל |

**שיחה חדשה** פותחת `thread_id` חדש, ואז «מה שמי?» חוזר ל«לא יודעת».

---

## איך נמנעים מ-Context Rot

1. **`scrape_url` חותך** ל-`MAX_SCRAPE_CHARS` (500) עם סימון `[נחתך: ...]`. הדף כולו לעולם לא נכנס להיסטוריה.
2. **`SummarizationMiddleware`**: ב-8 הודעות ההיסטוריה הישנה מוחלפת בהודעת סיכום, ונשארות 3 אחרונות. בשורת ההקשר רואים את מספר ההודעות יורד.
3. **תיאורי כלים קצרים**, חמישה כלים בלבד.
4. `SUMMARY_KEEP` לא נמוך מ-3: בערך קטן גם השאלה הנוכחית עלולה להיכנס לסיכום.

## מגבלות ידועות

- הסיכום בהדגמה המקומית מדומה, ולכן הוא מזכיר רק את השם. עם מודל אמיתי הוא עשיר יותר, ויכול גם לאבד פרטים.
- `ResearchAnswer` נבנה ב-Harness מתוך הכלים שהופעלו (מקורות) ומספר המקורות (`confidence`). עם מודל אמיתי אפשר להשתמש ב-`response_format` או `with_structured_output`.
- `InMemorySaver`: הזיכרון נמחק כשהתהליך נסגר. בפרודקשן SQLite או Postgres.
- אין rate limiting ואין caching לחיפושים.

---

## צ'קליסט פרויקט 2

**דרישות חובה**

- [x] 1. אייגנט ב-LangChain (`create_agent` + ReAct) — `agent.py`
- [x] 2. חיפוש רשת (Tavily או Firecrawl, עם stub) — `tools.py: web_search`
- [x] 3. סריקת דפים — `tools.py: scrape_url` (עם חיתוך)
- [x] 4. MCP Server חיצוני אחד לפחות — `server.py` + `MultiServerMCPClient`
- [x] 5. query rewrite — `tools.py: rewrite_query`, ו-System prompt שמחייב אותו לפני חיפוש
- [x] 6. זיכרון שיחה: Checkpointer + thread — `InMemorySaver`, `thread_id` לכל שיחה
- [x] 7. Trim או Summarize — `SummarizationMiddleware`

**Checklist מסירה**

- [x] README: איך מריצים, MCP, דוגמת session
- [x] לפחות 2 שיחות רב-הודעתיות (זיכרון עובד) — `check.py`
- [x] לוג tool calls (מה הופעל ולמה) — בחלון
- [x] 3 שאילתות מחקר שונות + מקורות בפלט
- [x] תיאור: איך נמנעו מ-Context Rot — למעלה

**בונוס**

- [x] פלט Pydantic: `ResearchAnswer`
- [ ] Skill ייעודי למחקר
- [ ] Routing: מתי KB פנימי / מתי web (קיים חלקית: MCP לפנימי, web לחיצוני)
- [x] UI ב-Gradio

---

## מיפוי לשיעורים

| שיעור | איפה בפרויקט |
|--------|--------------|
| 6 Skills | rewrite כ-tool (אפשר גם Skill) |
| 7 MCP | `server.py` + החיבור ב-`agent.py` |
| 8 תבניות | Agent (ReAct) עם סדר כלים מוגדר ב-System prompt |
| 9 Harness | `create_agent`, `@tool`, שגיאות כלי כ-Observation |
| 10 זיכרון + חיפוש | `InMemorySaver`, `SummarizationMiddleware`, חיפוש וסריקה |
