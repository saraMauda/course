# קובץ 3 – הפרומפט המועשר (Augmented)
# זה השלב שהופך אחזור ל-RAG: ההקשר נכנס לפרומפט, עם Guardrails.

ROLE = "את עוזרת תמיכה של חברת סלולר."

REFUSAL = "אני מצטערת, אך המקורות שסופקו אינם מכילים מספיק מידע."

NO_CONTEXT = "(לא נמצאו מקורות מספיק קרובים)"

RAG_TEMPLATE = """
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


def build_context(hits: list) -> str:
    if not hits:
        return NO_CONTEXT
    blocks = []
    for i, item in enumerate(hits, start=1):
        blocks.append(f"[מקור {i}] שאלה: {item['question']}\nתשובה: {item['answer']}")
    return "\n\n".join(blocks)


def build_prompt(question: str, hits: list) -> str:
    return RAG_TEMPLATE.format(
        role=ROLE,
        context=build_context(hits),
        question=question,
        refusal=REFUSAL,
    )
