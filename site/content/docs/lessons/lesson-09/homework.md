---
title: "שיעורי בית"
description: "שיעור 09 · פיתוח ב-LangChain – Harness, Tools ו-ReAct"
kind: "homework"
lesson: "09"
github: "https://github.com/saraMauda/course/tree/main/lessons/09-%D7%A9%D7%99%D7%A2%D7%95%D7%A8%D7%99-%D7%91%D7%99%D7%AA.md"
---

אותו דבר כמו בדמו של השיעור — רק במקום חברת סלולר, סוכן של **ספרייה עירונית**. את הכלים אני נותנת. **את ה-System prompt את כותבת בעצמך.**

לא בונות אפליקציה חדשה. לא מוסיפות עיצוב. לא נוגעות ב-`llm_client.py`, ב-`harness.py` וב-`ask_the_model.py`.

---

## המטרה

חלון Gradio שבו כותבות הודעה ורואות:

1. תשובה
2. מה נשלח למודל (כולל הכלים)
3. מה קרה מאחורי הקלעים

פעם **בלי Harness**, פעם **עם LangChain** — ו-**ה-System prompt שמחליט מתי כל כלי** כתוב על ידך.

---

## שלב 0 — העתקה

1. העתיקי את התיקייה `demos/09-langchain-harness` לתיקייה חדשה בשם `09-homework-library`.
2. **אל תעתיקי** את תיקיית `.venv`.

---

## שלב 1 — `tools.py`

מחקי את התוכן, והדביקי **בדיוק** את זה:

```python
# הכלים של ספרייה עירונית.
# כל כלי = פונקציה רגילה + @tool. השם והתיאור (docstring) הם מה שהמודל קורא.
# המודל לעולם לא נכנס לכאן. ה-Harness מריץ.

import ast
import json
import operator
import re

from langchain.tools import tool

ACCOUNTS = {
    "205": {
        "customer": "205",
        "note": "קנס איחור של 12 ₪ על הספר «הנסיך הקטן», 12 ימי איחור.",
    },
    "300": {
        "customer": "300",
        "note": "אין קנסות פתוחים.",
    },
}

ORDERS = {
    "41": {"order": "41", "note": "בקשה 41: הספר «הארי פוטר» ממתין לאיסוף בדלפק עד יום חמישי."},
    "52": {"order": "52", "note": "בקשה 52: הספר «הארי פוטר» בתור, צפוי בעוד כשבוע."},
}

KNOWLEDGE = [
    {"id": "late-fee", "text": "איחור: קנס של 1 ₪ ליום איחור, עד תקרה של 30 ₪. ביטול קנס רק אחרי אימות מול הדלפק."},
    {"id": "loan", "text": "השאלה: 21 יום, עד 5 ספרים. הארכה אחת של 14 יום, באפליקציה."},
    {"id": "card", "text": "כרטיס מנוי: הנפקה בדלפק עם תעודה מזהה. כרטיס אבוד מוחלף תמורת 10 ₪."},
]


@tool
def get_account(customer_id: str) -> str:
    """מחזיר את הקנסות ופרטי המנוי לפי מספר מנוי. השתמשי כשהמנוי שואל על קנס או חשבון ויש מספר מנוי."""
    key = customer_id.strip()
    data = ACCOUNTS.get(key, {"customer": key, "note": "המנוי לא במאגר."})
    return json.dumps(data, ensure_ascii=False)


@tool
def search_sources(query: str) -> str:
    """חיפוש במאגר הידע של הספרייה: איחורים, השאלות וכרטיסים. השתמשי כשצריך לדעת מה הנוהל. לא למידע על מנוי מסוים."""

    def words_of(text: str) -> set:
        return {w for w in re.findall(r"\w+", text) if len(w) > 2}

    words = words_of(query)
    scored = [(len(words & words_of(item["text"])), item) for item in KNOWLEDGE]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    best = [item for score, item in scored[:2] if score > 0]
    if not best:
        return "לא נמצא במאגר."
    return " ".join(f"[{item['id']}] {item['text']}" for item in best)


@tool
def lookup_order(order_id: str) -> str:
    """מחזיר מצב בקשת השאלה לפי מספר בקשה. השתמשי כשהמנוי שואל איפה הספר שביקש."""
    key = order_id.strip()
    if key == "13":
        # כשל מכוון: השירות "נופל". ה-Harness צריך להפוך את זה ל-Observation, לא לקריסה.
        raise TimeoutError("שירות הבקשות לא ענה בזמן")
    data = ORDERS.get(key, {"order": key, "note": "הבקשה לא במאגר."})
    return json.dumps(data, ensure_ascii=False)


@tool
def web_search(query: str) -> str:
    """חיפוש באינטרנט למידע עדכני שאינו במאגר הספרייה (חדשות, מזג אוויר). לא לשאלות על קנסות או בקשות."""
    # stub: בדמו אין רשת. בשיעור 10 מחליפים ב-Tavily / Firecrawl.
    return f"[stub] אין חיבור לרשת בדמו. כאן היו מופיעות תוצאות חיפוש עבור: {query}"


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    raise ValueError("ביטוי לא נתמך")


@tool
def calculator(expression: str) -> str:
    """מחשבון לחשבון פשוט (+ - * /), למשל «5*1». השתמשי לכל חישוב מספרי, אל תחשבי בראש."""
    value = _eval(ast.parse(expression, mode="eval"))
    return json.dumps({"result": round(value, 2)}, ensure_ascii=False)


TOOLS = [get_account, search_sources, lookup_order, web_search, calculator]
```

שמות הכלים **נשארים** כמו בדמו (`get_account`, `lookup_order`...). רק התוכן והתיאורים משתנים.

---

## שלב 2 — `prompt.py`

**א. ה-System prompt (החלק שלך).** מחקי את `SYSTEM_PROMPT` וכתבי אותו מחדש. חייבים להיות בו:

| חלק | מה צריך להיות |
|-----|----------------|
| תפקיד | «את עוזרת בספרייה עירונית», בעברית, קצר |
| «מתי כל כלי» | חמש שורות, אחת לכל כלי. כל שורה אומרת *מתי*, לא רק *מה* |
| כלל 1 | לא ממציאים קנס, סטטוס או נוהל. אם אין נתון, משתמשים בכלי |
| כלל 2 | אם חסר מספר מנוי או מספר בקשה, מבקשים אותו |
| כלל 3 | אם כלי נכשל, אומרים שלא הצלחת לבדוק כרגע. לא ממציאים תשובה |

(התבנית ב-`prompt.py` של הדמו היא הדוגמה. אל תעתיקי ממנה מילה במילה. שני לספרייה.)

**ב. הדוגמאות** — החליפי את `EXAMPLES` ו-`EXAMPLE_TEXT` בזה:

```python
EXAMPLES = [
    "למה חייבו אותי בקנס איחור? מספר מנוי 205",
    "מה המדיניות על השאלת ספרים?",
    "מה מצב בקשה מספר 13?",
    "כמה קנס על 5 ימי איחור? 5 כפול 1",
    "מה מזג האוויר בתל אביב?",
]
EXAMPLE_TEXT = EXAMPLES[0]
```

---

## שלב 3 — `app.py`

שני שינויים בטקסט שמופיע בחלון:

| חפשי | החליפי ל- |
|------|-----------|
| `שיעור 09 — כותבות` | `שיעורי בית 09 — כותבות` |
| `שני כלים, כלי אחד, כשל כלי, חישוב, כלי חיצוני` | `קנס, מדיניות, כשל כלי, חישוב, כלי חיצוני` |

---

## מה אסור לגעת בו

- `llm_client.py`, `harness.py`, `ask_the_model.py`
- מבנה החלון ב-Gradio
- לא משנות את `MAX_ITERATIONS`, לא מוסיפות כלי שישי, לא מוסיפות זיכרון או חיפוש רשת אמיתי (זה שיעור 10), ולא LangGraph (שיעור 11)

---

## איך בודקות שהצלחת

הרצי `python app.py` מתוך התיקייה החדשה. בכל בדיקה בחרי **עם LangChain**.

| # | הודעה | מה חייבים לראות ב«מה קרה» |
|---|-------|-----------------------------|
| 1 | קנס איחור, מנוי 205 | `get_account`, אחר כך `search_sources`, אחר כך תשובה סופית עם «12 ₪» |
| 2 | מה המדיניות על השאלת ספרים? | `search_sources` בלבד |
| 3 | מה מצב בקשה מספר 13? | `lookup_order` **נכשל** וחזר כ-Observation. התשובה: «לא הצלחתי לבדוק כרגע». אין קריסה |
| 4 | כמה קנס על 5 ימי איחור? | `calculator` |
| 5 | מה מזג האוויר בתל אביב? | `web_search` (תוצאת stub) |
| 6 | אותה הודעה כמו 1, מצב **בלי Harness** | תשובה בטוחה שמנחשת. אין כלים, ובפרומפט אין רשימת כלים |

אם בדיקה 1 לא קוראת לכלים — כנראה ה-`SYSTEM_PROMPT` ריק או נמחק לגמרי (בלי הוראות המודל המקומי עונה כמו «בלי Harness»).

> עם מודל אמיתי הבחירות יכולות להשתנות (למשל הוא יקרא ל-`search_sources` גם בבדיקה 1 וגם יתעלם ממנו). זה בסדר — תעדי מה קיבלת.

---

## שלוש ריצות להגשה

תעדי **שלוש ריצות**, כל אחת עם צילום של «מה קרה מאחורי הקלעים»:

1. **כלי נכון.** בדיקה 1 או 2.
2. **כלי שגוי שתוקן.** ב-`tools.py` שני את התיאור של `web_search` ל-«חיפוש בכל נושא». הריצי את בדיקה 2 וראי אם המודל עבר ל-`web_search` (עם מודל אמיתי סביר שכן; בהדגמה המקומית הבחירה קבועה, ותכתבי זאת). תקני את התיאור והריצי שוב.
3. **כשל כלי.** בדיקה 3.

---

## שאלות להגשה

1. **תיאור הוא פרומפט:** מה ההבדל בין «מחזיר קנסות לפי מספר מנוי» לבין התיאור המלא שבקובץ? מה התוספת עושה למודל? משפט או שניים.
2. **Harness:** כתבת בשיעור 3 לולאת ReAct ידנית. אילו שני דברים `create_agent` ו-`tool_errors_as_observation` עושים במקומך? (רמז: מי מריץ את הכלי, ומה קורה כשהוא נכשל.)
3. **לפרויקט 2:** ממשי Agent עם שני כלים לפחות: `web_search` (stub מותר) ו-`search_sources`. כתבי System prompt שמסביר מתי כל אחד, ותעדי שלוש ריצות באותו מבנה (נכון, שגוי שתוקן, כשל).

---

## מה מגישות

1. התיקייה `09-homework-library` (בלי `.venv`).
2. צילומי שלוש הריצות.
3. התשובות לשאלות 1–2, והפניה לתיקיית הפרויקט עבור שאלה 3.
