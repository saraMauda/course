# קובץ 2 – הפונקציה בעולם האמיתי
# המודל לעולם לא נכנס לכאן. הוא רק מבקש שנריץ. אנחנו מריצות.

import json
from datetime import datetime

WEATHER = {
    "tel aviv": (31, "חם ובהיר"),
    "תל אביב": (31, "חם ובהיר"),
    "jerusalem": (26, "מעונן חלקית"),
    "ירושלים": (26, "מעונן חלקית"),
    "eilat": (38, "שרב"),
    "אילת": (38, "שרב"),
}


def get_weather(location: str) -> str:
    temp, condition = WEATHER.get(
        location.strip().lower(),
        (22, "לא ידוע – העיר לא במאגר"),
    )
    result = {
        "location": location,
        "temp_c": temp,
        "condition": condition,
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
    }
    return json.dumps(result, ensure_ascii=False)
