# קובץ 1 – MCP Server
# שירות עצמאי שמספק Tools. הוא לא יודע איזה מודל או איזה Host יתחברו אליו.
# שימי לב: אסור להדפיס (print) מכאן – ה-stdout הוא ערוץ התקשורת של הפרוטוקול.

import json

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("telecom-support")

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


# ה-decorator הופך פונקציה רגילה ל-Tool שה-Client יכול לגלות ולהפעיל.
# שם הפונקציה, ה-docstring וסוגי הפרמטרים הופכים לתיאור שהמודל רואה.
@mcp.tool()
def lookup_bill(customer_id: str) -> str:
    """מחזיר את פירוט החיובים של לקוחה לפי מספר לקוחה. השתמשי בו לפני שעונים על שאלה על חיוב."""
    key = customer_id.strip()
    data = BILLS.get(key, {"customer": key, "error": "הלקוחה לא במאגר"})
    return json.dumps(data, ensure_ascii=False)


@mcp.tool()
def lookup_policy(topic: str) -> str:
    """מחזיר את מדיניות החברה בנושא נתון, למשל «חיוב כפול» או «החזר»."""
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
