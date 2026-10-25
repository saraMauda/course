---
title: "פרויקט 2"
description: "Autonomous Research Agent with MCP & Tools"
kind: "project"
---

> **סיכום חטיבה 2** · שיעורים 6–10  
> **תוצר:** אייג'נט מחקר ב-LangChain עם כלים, MCP וזיכרון

---

## 📌 תיאור התרגיל

בניית **אייג'נט מחקר אוטונומי** שמסוגל:

- לחפש מידע ברשת
- לסרוק דפים
- להשתמש ב-MCP חיצוני
- לשכתב שאילתות
- לנהל זיכרון שיחה בלי ליפול ל-Context Rot

---

## 🧩 דרישות (חובה)

| # | דרישה | שיעור |
|---|--------|--------|
| 1 | אייג'נט ב-LangChain (Harness + ReAct loop) | 9 |
| 2 | חיפוש רשת (Tavily **או** Firecrawl search/map) | 10 |
| 3 | סריקת דפים (Firecrawl scrape או שקול) | 10 |
| 4 | חיבור ל-**MCP Server** חיצוני אחד לפחות | 7, 9 |
| 5 | יכולת **query rewrite** (tool או Skill) | 6, 10 |
| 6 | זיכרון שיחה: Checkpointer + thread | 10 |
| 7 | מנגנון Trim **או** Summarize | 10 |

### בונוס
- Skill ייעודי למחקר (Progressive Disclosure)
- פלט Pydantic: `ResearchAnswer`
- Routing: מתי KB פנימי / מתי web
- UI ב-Streamlit/Gradio

---

## 🏗️ ארכיטקטורה מוצעת

```text
User
  → Host (LangChain Agent)
      → Tools: rewrite_query | web_search | scrape_url | (optional) search_sources
      → MCP Client → External Server
      → Checkpointer (InMemorySaver / SQLite)
      → Summarize middleware (optional)
  → Structured answer + sources
```

---

## 🛠️ שלבי פיתוח מומלצים

1. Agent + tool אחד + לולאה  
2. הוספת search + scrape  
3. MCP  
4. Memory + session  
5. Rewrite + סיכום הקשר  
6. מפרט בדיקות  

---

## 🧪 Checklist מסירה

- [ ] README: APIs, MCP איך להריץ, דוגמת session
- [ ] לפחות 2 שיחות רב-הודעתיות (זיכרון עובד)
- [ ] לוג tool calls (מה הופעל ולמה)
- [ ] 3 שאילתות מחקר שונות + מקורות בפלט
- [ ] תיאור: איך נמנעתם מ-Context Rot

---

## ✅ מיפוי חטיבה 2

| שיעור | יישום |
|--------|--------|
| 6 Skills | rewrite / research skill |
| 7 MCP | server מחובר |
| 8 Patterns | Agent + (אופצ.) parallel mental model |
| 9 Harness | create_agent + @tool |
| 10 Memory/Web | checkpointer + search stack |

---

## 📎 מקורות

- שיעורים `06`–`10` בתיקיית `lessons/`
- `18 LangChain - Project`, סיכומי LangChain / MCP / Skills
