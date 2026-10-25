# קובץ 2 – הכלים
# כל כלי = פונקציה רגילה + @tool. השם והתיאור (docstring) הם מה שהמודל קורא.
# התיאור הוא פרומפט: אומר *מתי* להשתמש, ולא רק מה הכלי עושה.
# המודל לעולם לא נכנס לכאן. ה-Harness מריץ.

import ast
import json
import operator
import re

from langchain.tools import tool

ACCOUNTS = {
    "312": {
        "customer": "312",
        "note": "שני חיובים זהים של 39.90 באותו חודש על חבילת גלישה.",
    },
    "100": {
        "customer": "100",
        "note": "חיוב אחד תקין של 39.90 ביולי. אין כפל.",
    },
}

ORDERS = {
    "88": {"order": "88", "note": "הזמנה 88 במסירה בתל אביב, צפויה היום עד 18:00."},
    "91": {"order": "91", "note": "הזמנה 91 התעכבה במחסן, צפויה מחר עד 12:00."},
}

# מאגר הידע. בפרויקט 1 זה היה חיפוש cosine על embeddings; כאן מילות מפתח, כדי שהדמו יישאר קטן.
KNOWLEDGE = [
    {"id": "double-charge", "text": "חיוב כפול: שני חיובים זהים באותו חודש על אותה חבילה. זכאות להחזר של חיוב אחד תוך 5 ימי עסקים, אחרי אימות."},
    {"id": "refund", "text": "החזר: רק אחרי אימות החיוב. לא מבטיחים סכום שלא מופיע בפירוט."},
    {"id": "cancel", "text": "ביטול מנוי: ההודעה בכתב או באפליקציה, והמנוי מסתיים בסוף מחזור החיוב."},
]


@tool
def get_account(customer_id: str) -> str:
    """מחזיר את פירוט החשבון והחיובים של לקוחה לפי מספר לקוח. השתמשי כשהלקוחה שואלת על חיוב או חשבון ויש מספר לקוח."""
    key = customer_id.strip()
    data = ACCOUNTS.get(key, {"customer": key, "note": "הלקוח לא במאגר."})
    return json.dumps(data, ensure_ascii=False)


@tool
def search_sources(query: str) -> str:
    """חיפוש במאגר הידע הפנימי של החברה: מדיניות, החזרים וביטולים. השתמשי כשצריך לדעת מה הנוהל. לא למידע על לקוחה מסוימת."""
    def words_of(text: str) -> set:
        return {w for w in re.findall(r"\w+", text) if len(w) > 2}  # בלי מילות קישור קצרות

    words = words_of(query)
    scored = []
    for item in KNOWLEDGE:
        score = len(words & words_of(item["text"]))
        scored.append((score, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    best = [item for score, item in scored[:2] if score > 0]
    if not best:
        return "לא נמצא במאגר."
    return " ".join(f"[{item['id']}] {item['text']}" for item in best)


@tool
def lookup_order(order_id: str) -> str:
    """מחזיר סטטוס הזמנה או משלוח לפי מספר הזמנה. השתמשי כשהלקוחה שואלת איפה ההזמנה."""
    key = order_id.strip()
    if key == "13":
        # כשל מכוון: שירות ההזמנות "נופל". ה-Harness צריך להפוך את זה ל-Observation, לא לקריסה.
        raise TimeoutError("שירות ההזמנות לא ענה בזמן")
    data = ORDERS.get(key, {"order": key, "note": "ההזמנה לא במאגר."})
    return json.dumps(data, ensure_ascii=False)


@tool
def web_search(query: str) -> str:
    """חיפוש באינטרנט למידע עדכני שאינו במאגר החברה (חדשות, מזג אוויר). לא לשאלות על חיובים או הזמנות."""
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
    """מחשבון לחשבון פשוט (+ - * /), למשל «39.90*2». השתמשי לכל חישוב מספרי, אל תחשבי בראש."""
    value = _eval(ast.parse(expression, mode="eval"))
    return json.dumps({"result": round(value, 2)}, ensure_ascii=False)


TOOLS = [get_account, search_sources, lookup_order, web_search, calculator]
