# קובץ 2 – שתי גרסאות פרומפט
# הגרסה "בלי Guardrails" היא הגרסה הישנה. ה-Eval יראה מה היא שוברת.

ROLE = "את עוזרת תמיכה של חברת סלולר."

REFUSAL = "אני מצטערת, אך המקורות שסופקו אינם מכילים מספיק מידע."

NO_CONTEXT = "(לא נמצאו מקורות מספיק קרובים)"

WITH_GUARDRAILS = """
{role} עני על שאלת המשתמשת בהתבסס אך ורק על ההקשר.

הקשר:
---
{context}
---

שאלה:
{question}

הוראות:
- השתמשי רק בהקשר.
- אם אין בהקשר מספיק מידע, עני בדיוק: "{refusal}"
- אל תשתמשי בידע קודם.
- היי תמציתית.
""".strip()

WITHOUT_GUARDRAILS = """
{role} עני על שאלת המשתמשת בעזרת ההקשר.

הקשר:
---
{context}
---

שאלה:
{question}
""".strip()


def build_context(hits: list) -> str:
    if not hits:
        return NO_CONTEXT
    blocks = []
    for i, item in enumerate(hits, start=1):
        blocks.append(f"[מקור {i}] שאלה: {item['question']}\nתשובה: {item['answer']}")
    return "\n\n".join(blocks)


def build_prompt(question: str, hits: list, guardrails: bool) -> str:
    template = WITH_GUARDRAILS if guardrails else WITHOUT_GUARDRAILS
    return template.format(
        role=ROLE,
        context=build_context(hits),
        question=question,
        refusal=REFUSAL,
    )
