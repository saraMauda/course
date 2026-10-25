# קובץ 3 – ה-Dataset (Golden set)
# שאלה + מה מצפים לקבל. נכתב לפני הקוד, ולא משתנה כדי לגרום לבדיקה לעבור.
#
# source = איזה פריט במאגר אמור להישלף (None = מחוץ לתחום, אסור שיישלף כלום)
# must_contain = מחרוזת שחייבת להופיע בתשובה

from prompt import REFUSAL

GOLDEN = [
    # פגיעה טובה / ניסוח אחר
    {"question": "נגמר לי האינטרנט בטלפון, איך מרחיבים?", "kind": "ניסוח אחר", "source": "data", "must_contain": "גלישה נוספת"},
    {"question": "חויבתי פעמיים החודש, מה מגיע לי?", "kind": "ניסוח אחר", "source": "double_bill", "must_contain": "5 ימי עסקים"},
    {"question": "יש לי חיוב כפול על חבילת גלישה", "kind": "מילה משותפת", "source": "double_bill", "must_contain": "5 ימי עסקים"},
    {"question": "איך מחליפים סים אחרי שהמכשיר נגנב", "kind": "פגיעה ישירה", "source": "sim", "must_contain": "חוסמים את הקו"},
    {"question": "מתי המוקד פתוח?", "kind": "ניסוח אחר", "source": "hours", "must_contain": "24/7"},
    {"question": "שכחתי את ה-PIN של הסים", "kind": "פגיעה ישירה", "source": "pin", "must_contain": "PUK"},
    {"question": "אני רוצה לבטל את המסלול", "kind": "ניסוח אחר", "source": "cancel", "must_contain": "מחזור החיוב"},
    {"question": "המסך נשבר לי, מה עושים?", "kind": "ניסוח אחר", "source": "screen", "must_contain": "יומיים"},
    {"question": "איך מפעילים נדידה בחו״ל?", "kind": "ניסוח אחר", "source": "roaming", "must_contain": "נדידה"},
    # מחוץ לתחום: חייבים לסרב
    {"question": "מה מזג האוויר?", "kind": "מחוץ לתחום", "source": None, "must_contain": REFUSAL},
    {"question": "תמליצי לי על מסעדה בתל אביב", "kind": "מחוץ לתחום", "source": None, "must_contain": REFUSAL},
    {"question": "איך מבשלים פסטה?", "kind": "מחוץ לתחום", "source": None, "must_contain": REFUSAL},
]
