# קובץ 2 – הפרומפט והכלי
# הקטלוג (name + description) הוא חלק מתיאור הכלי. ה-body לא כאן.

SYSTEM_PROMPT = """
את עוזרת תמיכה של חברת סלולר. עני בעברית, קצרה וברורה.

אם אחד ה-skills בקטלוג מתאים למשימה – הפעילי אותו עם activate_skill,
ועני לפי ההנחיות שיחזרו. אם אין skill מתאים – עני מהידע שלך.
""".strip()


def build_tool(catalog_text: str) -> dict:
    return {
        "type": "function",
        "function": {
            "name": "activate_skill",
            "description": (
                "ה-skills הבאים מכילים הנחיות מומחה למשימות ספציפיות. "
                "כשמשימה מתאימה לתיאור של skill, הפעילי אותו לפי השם "
                "כדי לטעון את ההנחיות המלאות.\n"
                "== Skills זמינים ==\n" + catalog_text
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "שם ה-skill בדיוק כפי שמופיע בקטלוג"}
                },
                "required": ["name"],
            },
        },
    }


EXAMPLES = [
    "תכתבי תשובה ללקוחה שחויבה פעמיים על חבילת גלישה והיא כועסת.",
    "סכמי לי את מדיניות הביטול: ביטול נכנס בסוף מחזור החיוב. החזר רק על חיוב כפול, תוך 5 ימי עסקים. אין החזר על שימוש שכבר נצרך.",
    "מה בירת צרפת?",
]
EXAMPLE_TEXT = EXAMPLES[0]
