# 12 | 💬 תהליכים מורכבים ב-LangGraph (Multi-Agent & Branching)

> **מבנה מפגש:** פתיחה 10' · תאוריה 25' · Lab Fan-out 40' · תרגול 15' · סיכום 10'  
> **חטיבה 3**

---

## 🌟 הקדמה

סוכן יחיד נחנק כשיש מומחיות מרובה ופעולות מקבילות.  
ב-LangGraph מפרקים ל**כמה צמתים/סוכנים**, מנהלים **State גלובלי**, ומסנכרנים עם **Fan-out / Fan-in**.

זה המימוש הגרפי של Parallelization ו-Orchestrator–Workers משיעור 8.

---

## 📌 Fan-out / Fan-in

```text
              ┌→ researcher_web ──┐
START → plan ─┼→ researcher_kb  ──┼→ synthesizer → END
              └→ researcher_mcp ──┘
```

| מושג | משמעות |
|------|--------|
| **Fan-out** | מצומת אחד לכמה צמתים במקביל |
| **Fan-in** | כמה צמתים מתכנסים לצומת אחד (אחרי שכולם סיימו) |

ב-State: כל researcher כותב לשדה משלו / ל-list עם reducer שטוח.

---

## 🤖 ארכיטקטורת Multi-Agent

| תפקיד | אחריות |
|-------|--------|
| **Router / Orchestrator** | מפרק משימה, קובע מי עובד |
| **Specialist agents** | RAG, Web, Citation, Summarizer… |
| **Synthesizer** | מאחד, מסיר כפילויות, מנסח |
| **(אופצ.) Critic** | Evaluator–Optimizer |

**תקשורת:** לא "צ'אט חופשי" בין סוכנים בלבד – אלא **כתיבה ל-State** ומעברי edges. זה צפוי יותר.

---

## 🗂️ State גלובלי מול מקומי

| | Global State | Local (צומת) |
|---|--------------|--------------|
| חיים | לאורך הגראף / thread | בתוך node בלבד |
| דוגמה | messages, sources, plan | משתני עזר, תוצאת כלי גולמית |
| סיכון | נפיחות Context Rot | אובדן מידע אם לא כותבים חזרה |

**נוהג טוב:**  
- Global: רק מה שהשלבים הבאים צריכים  
- Local: עיבוד כבד → כתיבת **תמצית** ל-global  

---

## 🛠️ דוגמת State ל-NotebookLM

```python
class NotebookState(TypedDict):
    messages: Annotated[list, add_messages]
    sources_meta: list[dict]      # id, title, status
    retrieved_chunks: list[str]
    web_snippets: list[str]
    draft_answer: str
    needs_human: bool
```

---

## 🛠️ Lab

### שלב 1
גראף: `plan → research_a → research_b → merge` (אפשר סדרתי קודם).

### שלב 2
הפכו את שני research ל-fan-out (או סימולציה: שני nodes ואז merge).

### שלב 3
כל researcher כותב לשדה נפרד; synthesizer קורא את שניהם.

### שלב 4
הוסיפו conditional: אם אין מספיק sources → חזרה ל-research (max 2 loops).

---

## 🧩 תכולה

- Fan-out / Fan-in
- Multi-agent roles
- Global vs local state
- חיבור לתבניות שיעור 8

---

## 💡 טיפים ו-Gotchas

- Fan-in דורש הבנה מתי כולם "מוכנים".
- אל תשתפו system prompts זהים לכל specialist – תנו זהות.
- הגבילו מקבילויות ב-API (rate limits).
- לדיבאג – שמות nodes ברורים + LangSmith (שיעור 14).

---

## ✅ לסיכום

- גראף מאפשר מקביליות ומומחיות בלי כאוס.
- State גלובלי ממושמע = הצלחת multi-agent.
- Synthesizer הוא צומת קריטי, לא "עוד tool".
- בהמשך: עצירה לאדם (HITL).

---

## 👩‍💻 קוד / קישורים

- דמו הכיתה: [`demos/12-langgraph-multi-agent`](../demos/12-langgraph-multi-agent/README.md)

---

## 🏠 תרגיל בית

1. **שיעורי בית 12** – אותו דמו, על ספרייה עירונית, עם כלל עצירה שכתוב על ידכן וטבלת קורא/כותב: [12-שיעורי-בית.md](12-שיעורי-בית.md).
2. **התקדמות בפרויקט 3:**

   1. ציירו גראף Multi-Agent ל-NotebookLM (RAG + Web + Merge).  
   2. הגדירו שדות State לכל צומת (מה קורא / מה כותב).  
   3. כתבו כלל עצירה: מתי מפסיקים לחפש ומתי ממשיכים.

---

## 📎 מקורות

- שיעור 8 (תבניות), שיעור 11 (יסודות גרף)
