---
title: "פרויקט 3 (סיום)"
description: "Enterprise NotebookLM Clone"
kind: "project"
---

> **סיכום חטיבה 3 + כל הקורס** · שיעורים 1–15  
> **תוצר:** מערכת NotebookLM מלאה עם מקורות, גראף, HITL וניטור

---

## 📌 תיאור התרגיל

בניית **מערכת NotebookLM** עובדת: העלאת מקורות, אינדוקס, שיחה מבוססת מקורות (+ הרחבה חיצונית), בקרה אנושית, זיכרון ומעקב ביצועים.

---

## 🧩 דרישות (חובה)

### 1. מקורות ו-RAG
- העלאת **מסמכים/מקורות מרובים**
- חיתוך (chunking) + Embeddings
- שמירה ב-VectorStore מותאם: **`SourceStore`**
- אחזור לפי מחברת / מקורות מאושרים

### 2. גראף LangGraph
- שילוב **RAG retrieval**
- **חיפוש חיצוני** (tool)
- לולאת **ReAct** (agent ↔ tools)
- (מומלץ) אפשרות הרחבת MCP

### 3. Human-in-the-Loop
- אישור מקורות **לפני** עיבוד/אינדוקס מלא
- אפשרות לדחות / לסנן מקור

### 4. זיכרון + ניטור
- **Checkpointer** לשיחה
- מעקב ב-**LangSmith** (traces לפחות; eval – בונוס חזק)

---

## 🏗️ מבנה פרויקט מוצע

```text
notebooklm/
  source_store.py      # ingest, chunk, embed, search
  graph.py             # State + nodes + compile
  chat.py              # API לשיחה / thread_id
  hitl.py              # approve/reject sources
  tools/
    search_sources.py
    web_search.py
    scrape.py
  ui/app.py            # Gradio/Streamlit
  data/
  README.md
```

---

## 🛠️ שלבי פיתוח מומלצים

| שלב | תוצר |
|-----|------|
| 1 | SourceStore על טקסטים בלבד |
| 2 | Chat graph: retrieve → answer (בלי tools) |
| 3 | ReAct + tools (web) |
| 4 | HITL על מקורות |
| 5 | Checkpointer + sessions |
| 6 | LangSmith + 8 מקרי בדיקה |

---

## 🧪 Checklist מסירה

- [ ] README: ארכיטקטורה, הרצה, env vars, דיאגרמת גרף
- [ ] לפחות 3 מקורות באינדקס במחברת דמו
- [ ] זרימת Approve: pending → approved → searchable
- [ ] שיחה: שאלה מכוסה + שאלה מחוץ למקורות
- [ ] tool חיצוני אחד לפחות (מופעל ב-trace)
- [ ] thread_id: המשך שיחה עם זיכרון
- [ ] קישור/צילום trace מ-LangSmith
- [ ] Guardrails: לא להמציא מתוך "ידע כללי" כשיש מקורות

### בונוס מצטיין
- Multi-agent fan-out (web + kb)
- Pydantic structured answer + citations
- Skill לסיכום מקורות
- MCP server מחובר
- Eval dataset רץ אוטומטית

---

## ✅ מיפוי מלא לקורס

| חטיבה | יכולת בפרויקט |
|--------|----------------|
| 1 | Embeddings, RAG, Guardrails, Structuring |
| 2 | Tools, MCP, Memory, Web research patterns |
| 3 | LangGraph, HITL, LangSmith, ארכיטקטורה |

---

## 📎 מקורות

- [`15-notebooklm-deep-dive.md`](/docs/lessons/lesson-15)  
- פרויקטים 1–2 כבסיס לקוד  
- שיעורים 11–14
