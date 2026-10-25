---
title: "שיעורי בית"
description: "שיעור 07 · תקשורת ופרוטוקולים – Model Context Protocol (MCP)"
kind: "homework"
lesson: "07"
github: "https://github.com/saraMauda/course/tree/main/lessons/07-%D7%A9%D7%99%D7%A2%D7%95%D7%A8%D7%99-%D7%91%D7%99%D7%AA.md"
---

אותו דבר כמו בדמו של השיעור — רק במקום חיובי סלולר, MCP Server של **ספרייה עירונית**.

לא בונות Host חדש. לא מוסיפות עיצוב. לא נוגעות ב-`client.py`, ב-`llm_client.py` ובלולאה ב-`ask_the_model.py`.

---

## המטרה

חלון Gradio שבו כותבות בקשה ורואות:

1. תשובה
2. מה נשלח למודל (כולל ה-Tools)
3. מה קרה מאחורי הקלעים

פעם **בלי MCP**, פעם **עם MCP** — כשהפעם **ה-Server כתוב על ידך**.

---

## שלב 0 — העתקה

1. העתיקי את התיקייה `demos/07-mcp` לתיקייה חדשה בשם `07-homework-library`.
2. **אל תעתיקי** את תיקיית `.venv`.

---

## שלב 1 — `server.py`

מחקי את התוכן, והדביקי **בדיוק** את זה:

```python
# MCP Server של ספרייה עירונית.
# שימי לב: אסור להדפיס (print) מכאן – ה-stdout הוא ערוץ התקשורת של הפרוטוקול.

import json

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("city-library")

BOOKS = {
    "הנסיך הקטן": {
        "title": "הנסיך הקטן",
        "copies": 3,
        "available": 2,
        "location": "מדור ילדים, מדף 4",
    },
    "הארי פוטר": {
        "title": "הארי פוטר",
        "copies": 2,
        "available": 0,
        "location": "מדור נוער, מדף 1",
        "back_on": "15 בחודש",
    },
}

POLICIES = {
    "השאלה": "השאלה ל-21 יום, עד 5 ספרים. הארכה אחת של 14 יום, באפליקציה.",
    "איחור": "קנס של 1 ₪ ליום איחור, עד תקרה של 30 ₪.",
}


@mcp.tool()
def lookup_book(title: str) -> str:
    """מחזיר זמינות של ספר בספרייה לפי שם הספר: כמה עותקים, כמה זמינים, ואיפה הוא במדף."""
    key = title.strip()
    data = BOOKS.get(key, {"title": key, "error": "הספר לא במאגר"})
    return json.dumps(data, ensure_ascii=False)


@mcp.tool()
def lookup_loan_policy(topic: str) -> str:
    """מחזיר את מדיניות הספרייה בנושא נתון, למשל «השאלה» או «איחור»."""
    topic = topic.strip()
    policy = POLICIES.get(topic)
    if policy is None:
        for name, text in POLICIES.items():
            if name in topic or topic in name:
                policy, topic = text, name
                break
    return json.dumps(
        {"topic": topic, "policy": policy or "לא נמצאה מדיניות בנושא."},
        ensure_ascii=False,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
```

שימי לב לשלושה דברים בלבד:

| בדמו של השיעור | אצלך |
|----------------|------|
| `lookup_bill(customer_id)` | `lookup_book(title)` |
| `lookup_policy(topic)` | `lookup_loan_policy(topic)` |
| חשבונות ומדיניות סלולר | ספרים ומדיניות ספרייה |

ה-docstring של כל פונקציה הוא **התיאור שהמודל קורא**. אל תשני אותו.

---

## שלב 2 — `ask_the_model.py`

שני שינויים בלבד, בראש הקובץ. **אל תשני את הלולאה.**

**א. `SYSTEM_PROMPT`** — החליפי בזה:

```python
SYSTEM_PROMPT = """
את עוזרת בספרייה עירונית. עני בעברית, קצרה וברורה.

אם צריך נתון על ספר או על מדיניות – השתמשי בכלים שעומדים לרשותך.
אל תמציאי זמינות, תאריך או מדיניות.
""".strip()
```

**ב. `EXAMPLES`** — החליפי בזה:

```python
EXAMPLES = [
    'האם הספר "הנסיך הקטן" זמין להשאלה?',
    'האם הספר "הארי פוטר" זמין להשאלה?',
    "מה מזג האוויר?",
]
```

---

## שלב 3 — `app.py`

שני שינויים בטקסט שמופיע בחלון:

| חפשי | החליפי ל- |
|------|-----------|
| `שיעור 07 — מבקשות` | `שיעורי בית 07 — מבקשות` |
| `חיוב כפול, חיוב תקין, לא קשור` | `ספר זמין, ספר לא זמין, לא קשור` |

---

## מה אסור לגעת בו

- `client.py` — הוא גנרי. אם צריך לשנות אותו בשביל שרת חדש, משהו השתבש.
- `llm_client.py`
- הלולאה ב-`ask_the_model.py` (`_ask_with_mcp`)
- מבנה החלון ב-Gradio
- לא מוסיפות Tool שלישי, שרת שני, LangChain או Playwright

---

## איך בודקות שהצלחת

הרצי `python app.py` מתוך התיקייה החדשה. **לא מפעילות את `server.py` ידנית.**

| # | בקשה | מצב | מה חייבים לראות |
|---|------|------|------------------|
| 1 | האם הספר "הנסיך הקטן" זמין להשאלה? | בלי MCP | תשובה בטוחה שמתארת הכל כזמין. ב«מה נשלח»: «לא חוברו שרתי MCP. אין Tools». |
| 2 | אותה בקשה | עם MCP | ב«מה קרה»: `list_tools` החזיר `lookup_book` ו-`lookup_loan_policy`. המודל בחר `lookup_book` ואחר כך `lookup_loan_policy`. התשובה: «2 מתוך 3 עותקים». |
| 3 | האם הספר "הארי פוטר" זמין להשאלה? | עם MCP | «לא זמין כרגע, צפוי לחזור ב-15 בחודש». |
| 4 | מה מזג האוויר? | עם MCP | אף Tool לא הופעל. |

אם בדיקה 2 נכשלת עם שגיאה — בדקי ש-`pip install -r requirements.txt` רץ (חבילת `mcp`), ושהקובץ נקרא `server.py` ויושב ליד `client.py`.

---

## שאלה קצרה להגשה

ה-Host שלך לא מכיר את `lookup_book`. מאיפה הוא יודע שהיא קיימת, ומה המודל קורא כדי להחליט להפעיל אותה? שני משפטים.

---

## מה מגישות

1. התיקייה `07-homework-library` (בלי `.venv`).
2. צילום מסך של בדיקה 2: הבקשה, התשובה, ו«מה קרה מאחורי הקלעים».
3. התשובה לשאלה הקצרה.
