---
title: "שיעורי בית"
description: "שיעור 01 · תשתית ומושגי יסוד בעולם ה-LLM"
kind: "homework"
lesson: "01"
github: "https://github.com/saraMauda/course/tree/main/lessons/01-%D7%A9%D7%99%D7%A2%D7%95%D7%A8%D7%99-%D7%91%D7%99%D7%AA.md"
---

אותו דבר כמו בדמו של השיעור — רק במקום מזג אוויר, כלי של **עיר בירה**.

לא בונות בוט חדש. לא מוסיפות עיצוב. לא נוגעות ב-`llm_client.py`.

---

## המטרה

חלון Gradio שבו כותבות שאלה ורואות:

1. תשובה
2. מה נשלח למודל (הפרומפט)
3. מה קרה מאחורי הקלעים

פעם **בלי כלים**, פעם **עם כלי** `get_capital`.

---

## שלב 0 — העתקה

1. העתיקי את התיקייה `demos/01-function-calling` לתיקייה חדשה בשם `01-homework-capital`.
2. **אל תעתיקי** את תיקיית `.venv`.
3. בתוך התיקייה החדשה: שמי את `weather_tool.py` ל-`capital_tool.py`.

---

## שלב 1 — `capital_tool.py`

מחקי את התוכן, והדביקי **בדיוק** את זה:

```python
# הפונקציה בעולם האמיתי.
# המודל לעולם לא נכנס לכאן. הוא רק מבקש שנריץ.

import json

CAPITALS = {
    "israel": "ירושלים",
    "ישראל": "ירושלים",
    "france": "פריז",
    "צרפת": "פריז",
    "japan": "טוקיו",
    "יפן": "טוקיו",
    "italy": "רומא",
    "איטליה": "רומא",
    "egypt": "קהיר",
    "מצרים": "קהיר",
    "spain": "מדריד",
    "ספרד": "מדריד",
}


def get_capital(country: str) -> str:
    capital = CAPITALS.get(
        country.strip().lower(),
        "לא ידוע – המדינה לא במאגר",
    )
    result = {
        "country": country,
        "capital": capital,
        "source": "המאגר שלנו",
    }
    return json.dumps(result, ensure_ascii=False)
```

שימי לב לשלושה דברים בלבד:

| בדמו של השיעור | אצלך |
|----------------|------|
| `get_weather` | `get_capital` |
| פרמטר `location` | פרמטר `country` |
| מילון ערים | מילון מדינות → בירות |

---

## שלב 2 — `prompt.py`

שלושה שינויים. תשאירי את שאר הקובץ כמו שהוא.

**א. הפרומפט** — החליפי את `SYSTEM_PROMPT` בזה:

```python
SYSTEM_PROMPT = """
את עוזרת בעברית, קצרה וברורה.

אם שואלים מה עיר הבירה של מדינה – חובה להפעיל את הכלי get_capital.
אל תעני מעצמך על עיר בירה, גם אם את יודעת.
אם אין צורך בכלי – עני מהידע שלך.
""".strip()
```

למה «חובה להפעיל»? כי בניגוד למזג אוויר, המודל **כן יודע** מה בירת צרפת. בלי המשפט הזה הוא עלול לדלג על הכלי.

**ב. הסכימה** — שמי `WEATHER_TOOL` ל-`CAPITAL_TOOL`, והחליפי את התוכן:

```python
CAPITAL_TOOL = {
    "type": "function",
    "function": {
        "name": "get_capital",
        "description": (
            "מחזיר את עיר הבירה של מדינה לפי המאגר שלנו. "
            "השתמשי בכלי הזה בכל שאלה על עיר בירה."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "country": {
                    "type": "string",
                    "description": "שם מדינה, למשל Japan או יפן",
                }
            },
            "required": ["country"],
        },
    },
}
```

**ג. שאלת ברירת המחדל:**

```python
EXAMPLE_QUESTION = "מה בירת יפן?"
```

---

## שלב 3 — `ask_the_model.py`

רק שמות. **אל תשני את הלולאה.**

חפשי והחליפי:

| חפשי | החליפי ל- |
|------|-----------|
| `from prompt import SYSTEM_PROMPT, WEATHER_TOOL` | `from prompt import SYSTEM_PROMPT, CAPITAL_TOOL` |
| `from weather_tool import get_weather` | `from capital_tool import get_capital` |
| `WEATHER_TOOL` | `CAPITAL_TOOL` |
| `get_weather` | `get_capital` |

אחרי ההחלפה אמורה להיות שורה כזו:

```python
tools = [CAPITAL_TOOL] if use_tools else None
```

ושורה כזו:

```python
result = get_capital(**json.loads(call.function.arguments))
```

---

## שלב 4 — `app.py`

שני שינויים בטקסט שמופיע בחלון:

| חפשי | החליפי ל- |
|------|-----------|
| `עם כלי get_weather` | `עם כלי get_capital` |
| `שיעור 01 — שואלות` | `שיעורי בית 01 — שואלות` |

---

## מה אסור לגעת בו

- `llm_client.py`
- מבנה החלון ב-Gradio (לא מוסיפות כפתורים, לא CSS)
- הלולאה ב-`ask()` — רק שמות הכלי

---

## איך בודקות שהצלחת

הרצי `python app.py` מתוך התיקייה החדשה.

| # | שאלה | מצב | מה חייבים לראות |
|---|------|------|------------------|
| 1 | מה בירת יפן? | בלי כלים | תשובה מהזיכרון. ב«מה נשלח» כתוב: לא נשלחו כלים. ב«מה קרה» אין הרצת פונקציה. |
| 2 | מה בירת יפן? | עם כלי | ב«מה קרה» יש `get_capital`. התוצאה מהקוד כוללת `"source": "המאגר שלנו"`. |
| 3 | כמה זה 2+2? | עם כלי | המודל עונה בלי להפעיל כלי. |

אם בדיקה 2 לא מפעילה כלי — חזרי ל-`SYSTEM_PROMPT`. חסר שם המשפט «חובה להפעיל».

---

## מה מגישות

1. התיקייה `01-homework-capital` (בלי `.venv`).
2. צילום מסך של בדיקה 2: השאלה, התשובה, ו«מה קרה מאחורי הקלעים».
