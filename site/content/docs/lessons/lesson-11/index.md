---
title: "מבוא ל-LangGraph – State Machines ואייג'נטים כגראף"
description: "בסיס לפרויקט 3 (NotebookLM)"
kind: "lesson"
lesson: "11"
division: 3
schedule: ["פתיחה 10'","תאוריה 25'","Lab ReAct Graph 40'","תרגול 15'","סיכום 10'"]
hasHomework: "yes"
github: "https://github.com/saraMauda/course/tree/main/lessons/11-langgraph-basics.md"
---

## 🌟 הקדמה

LangChain מצוינת ל-Harness מהיר. אבל כשהבקרה הופכת לקריטית – הסתעפויות, חזרות, עצירות, multi-agent – צריך **גראף מפורש**.

**LangGraph** = סוכנים ותהליכים כ-**State Machine**: צמתים, קשתות, ותנאי מעבר על **State** משותף.

---

## 🆕 מתי LangChain "לא מספיקה"?

| סימן | משמעות |
|------|--------|
| לולאות מורכבות עם תנאים | צריך Conditional Edges |
| כמה מסלולים במקביל | Fan-out / Fan-in (שיעור 12) |
| עצירה לאישור אדם | HITL / breakpoints (שיעור 13) |
| דיבאג מסלול מדויק | גראף + traces (LangSmith, 14) |
| State עשיר מעבר ל-messages | State definition רשמי |

---

## 📌 רכיבי היסוד

| רכיב | תפקיד |
|------|--------|
| **State** | TypedDict / dataclass – מה "זוכר" הגראף (messages, sources, flags…) |
| **Node** | פונקציה: `(state) -> partial state update` |
| **Edge** | מעבר קבוע מ-A ל-B |
| **Conditional Edge** | מעבר לפי לוגיקה / פלט מודל |
| **START / END** | כניסה ויציאה |
| **Compile** | בניית runnable + (אופציונלי) checkpointer |

```text
START → agent → tools? ──yes──→ tool_node ──┐
                  │                          │
                  no                         │
                  ↓                          │
                 END ←───────────────────────┘
```

---

## 🔁 ReAct Loop כגראף

### רעיון
- Node `agent`: קורא למודל עם tools bound  
- Node `tools`: מריץ tool calls  
- Conditional: אם יש tool_calls → tools, אחרת → END  

זה **אותו** ReAct משיעורים 3/9 – רק שקוף ושלוט.

### שלד קונספטואלי

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

def agent_node(state: State):
    # response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def tools_node(state: State):
    # execute tool calls from last message
    return {"messages": tool_results}

def should_continue(state: State):
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END

g = StateGraph(State)
g.add_node("agent", agent_node)
g.add_node("tools", tools_node)
g.add_edge(START, "agent")
g.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
g.add_edge("tools", "agent")
app = g.compile(checkpointer=InMemorySaver())
```

---

## 🛠️ Lab

### שלב 1
State עם `messages` בלבד + node יחיד שמחזיר תשובה.

### שלב 2
הוסיפו tool אחד + tool node + conditional edge.

### שלב 3
הריצו עם `thread_id` ו-checkpointer – המשיכו שיחה.

### שלב 4
ציירו את הגראף (Mermaid / `get_graph().draw_mermaid()` אם זמין).

---

## 🧩 תכולה

- למה LangGraph
- Nodes, Edges, Conditional Edges, State
- ReAct Graph מאפס
- Compile + checkpointer בסיסי

---

## 💡 טיפים ו-Gotchas

- עדכוני State הם **מיזוג** – הבינו reducers (`add_messages`).
- Node צריך להחזיר רק מה שמשתנה.
- אל תערבבו לוגיקה עסקית ענקית ב-conditional – שמרו קריא.
- גרסאות API משתנות – בדקו docs לגרסה שלכם.

---

## ✅ לסיכום

- LangGraph = בקרה מפורשת על זרימה.
- ReAct הוא תבנית גרף פשוטה וחזקה.
- State + Checkpointer = בסיס ל-HITL ולמולטי-agent.
- בשיעור הבא: מקביליות וריבוי סוכנים.

---

## 👩‍💻 קוד / קישורים

- דמו הכיתה: [`demos/11-langgraph-basics`](https://github.com/saraMauda/course/tree/main/demos/11-langgraph-basics/README.md)

---

## 🏠 תרגיל בית

1. **שיעורי בית 11** – אותו דמו, על ספרייה עירונית, עם Reducer וקשת מותנית שכתובים על ידכן: [11-שיעורי-בית.md](11-שיעורי-בית.md).
2. **התקדמות בפרויקט 3:**

   1. ממשו ReAct graph עם tool `search_sources` (או mock).  
   2. הוסיפו לשדה State: `sources: list[str]`.  
   3. שמרו דיאגרמת הגראף ל-README העתידי של NotebookLM.

---

## 📎 מקורות

- LangGraph docs  
- חיבור לשיעורים 3 (ReAct), 9 (Harness)
