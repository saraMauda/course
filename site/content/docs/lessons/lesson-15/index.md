---
title: "ארכיטקטורת קצה-לקצה וסיכום הקורס (NotebookLM Deep Dive)"
description: "גשר ל-פרויקט 3"
kind: "lesson"
lesson: "15"
division: 3
schedule: ["פתיחה 10'","ארכיטקטורה 30'","Code walkthrough 40'","סיכום קורס 20'"]
hasHomework: "yes"
github: "https://github.com/saraMauda/course/tree/main/lessons/15-notebooklm-deep-dive.md"
---

## 🌟 הקדמה

**NotebookLM** (ברמת הרעיון): מחברת חכמה מעל **מקורות** שהמשתמש מעלה – שואלים, מסכמים, חוקרים, תוך הישענות על החומר (ולעתים הרחבה לweb).

בשיעור נפרק ארכיטקטורת **Enterprise-style clone** שמשלבת את **כל חלקי הקורס**:

```text
RAG + Tools + MCP + LangGraph + HITL + Memory + LangSmith
```

---

## 🗺️ ארכיטקטורה מקצה לקצה

```text
┌─────────────────────────────────────────────────────────┐
│  UI (Gradio / Streamlit / Web)                          │
│  upload sources · approve · chat                        │
└────────────┬───────────────────────────────┬────────────┘
             │                               │
             ▼                               ▼
   ┌─────────────────┐              ┌─────────────────┐
   │  Source Pipeline│              │  Chat Graph     │
   │  parse/chunk    │              │  LangGraph      │
   │  embed/index    │◄──HITL───────│  ReAct + RAG    │
   │  SourceStore    │              │  Web tools/MCP  │
   └─────────────────┘              │  Checkpointer   │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │   LangSmith     │
                                    └─────────────────┘
```

---

## 📦 רכיבי מפתח

### `SourceStore`
שכבת VectorStore מותאמת למחברת:

| אחריות | פירוט |
|--------|--------|
| ingest | קבלת PDF/MD/URL/טקסט |
| chunk | אסטרטגיית חיתוך (שיעור 4–5) |
| embed | מודל אחיד |
| persist | אינדקס + מטא-דאטה (title, hash, approved) |
| retrieve | top-K לפי notebook_id / source_ids |

### `chat.py` (או מודול שיחה)
- טוען graph מהודר
- מעביר `thread_id` לכל משתמש/מחברת
- מזרים הודעות ל-State
- מחזיר תשובה + citations

### טעינת מקורות מרובים
- queue עיבוד
- סטטוסים: `pending → approved → indexed → error`
- HITL לפני `indexed` (שיעור 13)

---

## 🔁 גראף השיחה (תמצית)

```text
START
  → retrieve (SourceStore)
  → (optional) web_search / MCP
  → agent (synthesize + cite)
  → END
```

או ReAct מלא:

```text
agent ↔ tools(search_sources, web_search, scrape, mcp_*)
```

עם Evaluator אופציונלי: faithfulness למקורות.

---

## 🧩 מיפוי הקורס → מערכת

| שיעור | איפה במערכת |
|--------|-------------|
| 1 Function Calling | כל tool call בגרף |
| 2–3 Prompting | system prompts, guardrails, structuring |
| 4–5 RAG | SourceStore pipeline |
| 6 Skills | skill לסיכום / ציטוט / rewrite |
| 7 MCP | מקורות/פעולות חיצוניים |
| 8 Patterns | orchestrate researchers |
| 9–10 Harness/Memory | tools + checkpointer + summarize |
| 11–12 LangGraph | chat + multi-branch |
| 13 HITL | approve sources |
| 14 LangSmith | traces + eval suite |

---

## 🛠️ Code Walkthrough – סדר קריאה מומלץ

1. הגדרת `NotebookState`  
2. `SourceStore.add_source` / `similarity_search`  
3. Nodes: `retrieve`, `agent`, `tools`  
4. Compile עם checkpointer  
5. API/UI: upload → approve → chat  
6. Env: מפתחות + LangSmith  

---

## ✅ סיכום הקורס – משפטי עוגן

1. **מודל לבד לא מספיק** – צריך הקשר, כלים ובקרה.  
2. **Context Rot** מאיים על כל שכבה – Skills, chunking, trim.  
3. **Agent = Model + Harness**.  
4. **Workflow לפני Agent** כשאפשר; גראף כשצריך שליטה.  
5. **HITL + Eval** הופכים POC למערכת שאפשר לסמוך עליה.

---

## 👩‍💻 קוד / קישורים

- דמו הכיתה (שלד עובד): [`demos/15-notebooklm`](https://github.com/saraMauda/course/tree/main/demos/15-notebooklm/README.md)

---

## 🏠 תרגיל בית

1. **שיעורי בית 15** – אותו דמו, על ספרייה עירונית, עם אסטרטגיית חיתוך שכתובה על ידכן: [15-שיעורי-בית.md](15-שיעורי-בית.md).
2. **פרויקט 3** – ראו למטה.

---

## 🏠 מעבר לפרויקט 3

השתמשו בשיעור הזה כמפת דרכים. המפרט המלא:  
[`../projects/project-03-notebooklm.md`](/docs/projects/project-03)

---

## 📎 מקורות

- כל שיעורי `lessons/`
- פרויקטים 1–2 כרכיבים לשימוש חוזר (RAG, research tools)
