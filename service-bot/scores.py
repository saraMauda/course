"""כיול הסף: מדפיס את ציוני השליפה בלי לקרוא ל-LLM. הריצו, והחליטו על SCORE_THRESHOLD ב-config.py."""
from bot import retrieve

IN_SCOPE = ["איבדתי את הפלאפון שלי", "כמה עולה לגלוש בחו\"ל", "רוצה לעזוב את החברה", "החשבון החודשי יצא מוגזם"]
OUT_OF_SCOPE = ["מה מזג האוויר מחר?", "איך מכינים פסטה?", "מי ניצח בבחירות?"]

for label, qs in (("בתחום", IN_SCOPE), ("מחוץ לתחום", OUT_OF_SCOPE)):
    print(f"\n=== {label} ===")
    for q in qs:
        top = retrieve(q, 1)[0]
        print(f"{top['score']:.3f}  {q}  ->  {top['question']}")
