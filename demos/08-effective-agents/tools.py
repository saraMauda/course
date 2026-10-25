# קובץ 2 – המידע והפעולות בעולם האמיתי
# המודל לעולם לא נכנס לכאן. ב-Agent הוא מבקש ואנחנו מריצות.
# ב-Workflow אפילו הוא לא מבקש: הקוד קורא לפונקציות בעצמו.

import json
import re

ACCOUNTS = {
    "312": {
        "customer": "312",
        "plan": "חבילת גלישה",
        "month": "יולי",
        "amount": "39.90",
        "note": "שני חיובים זהים של 39.90 באותו חודש על חבילת גלישה.",
        "refund_eligible": True,
    },
    "100": {
        "customer": "100",
        "plan": "חבילת גלישה",
        "month": "יולי",
        "amount": "39.90",
        "note": "חיוב אחד תקין של 39.90 ביולי. אין כפל.",
        "refund_eligible": False,
    },
}

ORDERS = {
    "88": {
        "order": "88",
        "status": "במסירה",
        "eta": "היום עד 18:00",
        "note": "הזמנה 88 במסירה בתל אביב, צפויה היום עד 18:00.",
    },
    "91": {
        "order": "91",
        "status": "התעכבה",
        "eta": "מחר עד 12:00",
        "note": "הזמנה 91 התעכבה במחסן, צפויה מחר עד 12:00.",
    },
}

POLICIES = {
    "חיוב כפול": (
        "אם יש שני חיובים זהים באותו חודש על אותה חבילה – "
        "זכאות להחזר של חיוב אחד תוך 5 ימי עסקים, אחרי אימות."
    ),
    "החזר": "החזר רק אחרי אימות החיוב. לא מבטיחים סכום שלא מופיע בפירוט.",
}

_ACCOUNT_RE = re.compile(r"(?:לקוח|מנוי|חבר)\s*(?:מספר\s*)?(\d+)")
_ORDER_RE = re.compile(r"(?:הזמנה|השאלה|בקשה)\s*(?:מספר\s*)?(\d+)")


def extract_account_id(text: str) -> str | None:
    m = _ACCOUNT_RE.search(text or "")
    return m.group(1) if m else None


def extract_order_id(text: str) -> str | None:
    m = _ORDER_RE.search(text or "")
    return m.group(1) if m else None


def guess_policy_topic(text: str) -> str | None:
    """כלל פשוט של הקוד (לא של המודל): איזה נושא מדיניות מתאים להודעה."""
    if any(w in text for w in ("פעמיים", "כפול")):
        return "חיוב כפול"
    if any(w in text for w in ("החזר", "זיכוי")):
        return "החזר"
    return None


def lookup_account(account_id: str) -> str:
    key = account_id.strip()
    data = ACCOUNTS.get(key, {"customer": key, "error": "הלקוח לא במאגר"})
    return json.dumps(data, ensure_ascii=False)


def lookup_order(order_id: str) -> str:
    key = order_id.strip()
    data = ORDERS.get(key, {"order": key, "error": "ההזמנה לא במאגר"})
    return json.dumps(data, ensure_ascii=False)


def lookup_policy(topic: str) -> str:
    topic = topic.strip()
    policy = POLICIES.get(topic)
    if policy is None:
        for name, text in POLICIES.items():
            if name in topic or topic in name:
                policy, topic = text, name
                break
    if policy is None:
        return json.dumps({"topic": topic, "error": "לא נמצאה מדיניות בנושא."}, ensure_ascii=False)
    return json.dumps({"topic": topic, "policy": policy}, ensure_ascii=False)


def run_action(name: str, action_input: str) -> str:
    if name == "lookup_account":
        return lookup_account(action_input)
    if name == "lookup_policy":
        return lookup_policy(action_input)
    if name == "lookup_order":
        return lookup_order(action_input)
    return json.dumps({"error": f"פעולה לא מוכרת: {name}"}, ensure_ascii=False)
