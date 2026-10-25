# קובץ 2 – הפעולות בעולם האמיתי
# המודל לעולם לא נכנס לכאן. הוא רק מבקש שנריץ. אנחנו מריצות.

import json

BILLS = {
    "312": {
        "customer": "312",
        "plan": "חבילת גלישה",
        "month": "יולי",
        "charges": [39.90, 39.90],
        "note": "שני חיובים זהים באותו חודש",
    },
    "100": {
        "customer": "100",
        "plan": "חבילת גלישה",
        "month": "יולי",
        "charges": [39.90],
        "note": "חיוב אחד תקין",
    },
}

POLICIES = {
    "חיוב כפול": (
        "אם יש שני חיובים זהים באותו חודש על אותה חבילה – "
        "זכאות להחזר של חיוב אחד תוך 5 ימי עסקים. "
        "אין להבטיח החזר לפני אימות החיוב."
    ),
    "החזר": (
        "החזר רק אחרי אימות החיוב. "
        "נציגה לא מבטיחה סכום שלא מופיע בפירוט."
    ),
}


def lookup_bill(customer_id: str) -> str:
    key = customer_id.strip()
    data = BILLS.get(key, {"customer": key, "error": "הלקוח לא במאגר"})
    return json.dumps(data, ensure_ascii=False)


def lookup_policy(topic: str) -> str:
    topic = topic.strip()
    policy = POLICIES.get(topic)
    if policy is None:
        for name, text in POLICIES.items():
            if name in topic or topic in name:
                policy = text
                topic = name
                break
    if policy is None:
        policy = "לא נמצאה מדיניות בנושא."
    return json.dumps({"topic": topic, "policy": policy}, ensure_ascii=False)


def run_action(name: str, action_input: str) -> str:
    if name == "lookup_bill":
        return lookup_bill(action_input)
    if name == "lookup_policy":
        return lookup_policy(action_input)
    return json.dumps({"error": f"פעולה לא מוכרת: {name}"}, ensure_ascii=False)
