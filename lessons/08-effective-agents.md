# 08 | 💬 תבניות חשיבה ואייג'נטים (Effective Agents & Workflows)

> **מבנה מפגש:** פתיחה 10' · תאוריה 30' · תרשימי תבניות + דיון 30' · תרגול 20' · סיכום 10'  
> **חטיבה 2** · בסיס ל-LangChain/LangGraph

---

## 🌟 הקדמה

### מסע אחר ההגדרה: מהו Agent?

| שלב | הגדרה |
|-----|--------|
| טרום-אייג'נט | רק מודל, אין אייג'נט |
| אפליקציית LLM | UI סביב מודל |
| ReAct | לולאה: חשיבה → פעולה → תצפית (הגדרה **התנהגותית**) |
| Tool Calling מאומן | היכולת **מובנית** במודל, לא רק טריק פרומפט |
| Model + Tools + Memory | הגדרה **קומפוזיציונית** |
| Building Effective Agents | **שליטה בזרימה**: קוד או מודל? |
| Agent Harness | **Agent = Model + Harness** (שכבת ההנדסה) |

---

## 🔀 Workflows מול Agents

מהמאמר של Anthropic – *Building Effective Agents*:

| | **Workflow** | **Agent** |
|---|--------------|-----------|
| מי שולט | **הקוד** – נתיבים קבועים מראש | **המודל** – מנווט דינמית |
| צפיות | גבוהה, קל לבדיקה | גמישה, קשה יותר לחזות |
| מתי | תהליך ידוע, רגולטורי, עלות נמוכה | משימות פתוחות, מחקר, תקלות מגוונות |

**כלל אצבע:** התחילו ב-Workflow פשוט. עברו ל-Agent רק כשהמורכבות **דורשת** אוטונומיה.

---

## 🏗️ תבניות עבודה מתקדמות

### 1. Routing
מסווגים את הבקשה ושולחים ל"מסלול" מתאים.

```text
שאלה → Router → [תמיכה טכנית | חיוב | מכירות | מחוץ לתחום]
```

**Use-case:** מוקד שירות / חלוקת tickets.

### 2. Parallelization
מריצים כמה ענפים במקביל וממזגים.

```text
         ┌→ חוקר מקור א ─┐
שאלה ──→ ┼→ חוקר מקור ב ─┼→ מאגד תשובה
         └→ חוקר מקור ג ─┘
```

**Use-case:** מחקר מרובה מקורות, השוואת הצעות מחיר.

### 3. Orchestrator–Workers
מנהל מפרק משימה, מחלק לעובדים, מרכיב תוצר.

```text
Orchestrator → Worker_A (קוד)
             → Worker_B (בדיקות)
             → Worker_C (דוק)
             → סינתזה
```

**Use-case:** פיצ'ר מקצה לקצה, דוח מחקר עם פרקים.

### 4. Evaluator–Optimizer
לולאת יצירה + ביקורת + שיפור עד סף.

```text
Generator → Candidate
     ↑         ↓
     └── Evaluator (pass/fail + feedback)
```

**Use-case:** ניסוח מייל, קוד שעובר lint/tests, סיכום שנאמן למקור.

---

## 🖼️ מתי מה בוחרים?

```text
תהליך ידוע + שלבים קבועים     → Workflow / Chaining
סיווג פשוט לכמה נתיבים       → Routing
כמה מקורות / משימות עצמאיות  → Parallelization
משימה מורכבת + מומחיות מרובה → Orchestrator–Workers
איכות קריטית + מדד ברור      → Evaluator–Optimizer
מרחב פעולה פתוח + כלים       → Agent (ReAct + Tools)
```

---

## 🛠️ Lab (ללא framework כבד)

1. ציירו Routing לבוט התמיכה של פרויקט 1 (3 מסלולים).  
2. תכננו Parallel research: 2 "workers" + מאגד – מה כל אחד מביא.  
3. הגדירו קריטריון Evaluator לתשובת RAG: "רק מהקשר / ציטוט / אין הזיה".

---

## 🧩 תכולה

- אבולוציית הגדרת Agent
- Workflow vs Agent
- ארבע תבניות Anthropic
- בחירת תבנית לפי בעיית מוצר

---

## 💡 טיפים ו-Gotchas

- Agent יקר יותר (טוקנים + latency) ולא תמיד מדויק יותר.
- Parallelization בלי מאגד טוב = סתירות.
- Evaluator חלש = לולאה אינסופית; הגדירו max iterations.
- בהמשך: LangGraph מממש תבניות אלה ב-Nodes/Edges.

---

## ✅ לסיכום

- ההגדרה הבשלה: מי שולט בזרימה + מה ה-Harness.
- Workflows לפני Agents כשאפשר.
- Routing, Parallel, Orchestrator–Workers, Evaluator–Optimizer = ערכת כלים ארכיטקטונית.
- בפרויקט 2 תשלב בין Routing/ReAct + כלים חיצוניים.

---

## 👩‍💻 קוד / קישורים

- דמו הכיתה: [`demos/08-effective-agents`](../demos/08-effective-agents/README.md)

---

## 🏠 תרגיל בית

1. **שיעורי בית 08** – אותו דמו, על ספרייה עירונית, עם השוואה בין ארבע התבניות: [08-שיעורי-בית.md](08-שיעורי-בית.md).
2. **התקדמות בפרויקט 2:**

   1. בחרו תבנית ראשית ל-Research Agent (לרוב: Agent + Parallel search רעיוני).  
   2. כתבו 5 כללי ניתוב (מתי חיפוש רשת / מתי MCP / מתי תשובה ישירה).  
   3. הגדירו Evaluator: "מספיק מקורות? עדכניות? ציטוטים?"

---

## 📎 מקורות

- https://www.anthropic.com/engineering/building-effective-agents  
- `Lang chain סיכום אישי`
