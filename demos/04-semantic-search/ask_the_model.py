# קובץ 3 – החיפוש במאגר
# בלי סמנטי: התאמת מחרוזות.
# עם סמנטי: embedding לשאילתה + דירוג cosine.

from catalog import ITEMS
from llm_client import embedding_model_name, notice
from search import MIN_SCORE, embedding_trace, keyword_search, semantic_search


def _prompt_text(query: str, use_semantic: bool, rows: list) -> str:
    lines = []
    if use_semantic:
        lines.append("מצב: חיפוש סמנטי")
        lines.append(f"מודל embedding: {embedding_model_name()}")
        lines.append("אותו מודל לשאילתה ולכל פריט במאגר.")
        lines.append("")
        lines.append(f"הוטמע (שאילתה): {query}")
        lines.append("הוטמע (פריטי המאגר):")
        for item in ITEMS:
            lines.append(f"- [{item['id']}] {item['question']}")
        lines.append("")
        lines.append("דירוג cosine (גבוה = אותה זווית, לא בהכרח תשובה עסקית נכונה):")
        for item in rows:
            score = item.get("score")
            lines.append(f"- {score:.2f}  [{item['id']}] {item['question']}")
    else:
        lines.append("מצב: חיפוש מילולי")
        lines.append("אין embedding. בודקים האם המחרוזת או מילים ממנה מופיעות בשאלה/תשובה.")
        lines.append("")
        lines.append(f"חיפשו במאגר: {query}")
        lines.append("פריטים שנבדקו:")
        for item in ITEMS:
            lines.append(f"- [{item['id']}] {item['question']}")
        lines.append("")
        if rows:
            lines.append("התאמות מילוליות:")
            for item in rows:
                matched = ", ".join(item.get("matched") or [])
                lines.append(f"- [{item['id']}] {item['question']}" + (f"  ({matched})" if matched else ""))
        else:
            lines.append("אין התאמה מילולית.")
    return "\n".join(lines)


def ask(text: str, use_semantic: bool) -> dict:
    query = (text or "").strip()
    steps = [f"1. המשתמשת חיפשה: {query}"]

    if not use_semantic:
        steps.append("2. מצב: חיפוש מילולי. אין embedding, רק התאמת מחרוזות.")
        steps.append(f"3. נבדקו {len(ITEMS)} פריטים במאגר.")
        hits = keyword_search(query, ITEMS)
        if not hits:
            steps.append("4. אף פריט לא הכיל את המילים מהשאילתה.")
            steps.append("5. אין התאמה מילולית – לא ממציאים תשובה.")
            return {
                "answer": "לא מצאתי מקור מתאים בחיפוש מילולי.",
                "prompt": _prompt_text(query, False, []),
                "what_happened": "\n".join(steps),
                "embedding": "",
                "notice": notice(),
            }
        steps.append("4. נמצאו פריטים עם מילים משותפות:")
        for item in hits:
            matched = ", ".join(item.get("matched") or [])
            steps.append(f"   - [{item['id']}] {item['question']} ({matched})")
        best = hits[0]
        steps.append(f"5. נבחר [{best['id']}] כי היו בו הכי הרבה מילים משותפות.")
        return {
            "answer": f"{best['answer']}\n\n(מקור: {best['question']})",
            "prompt": _prompt_text(query, False, hits),
            "what_happened": "\n".join(steps),
            "embedding": "",
            "notice": notice(),
        }

    steps.append("2. מצב: חיפוש סמנטי. embedding לשאילתה ולכל פריט, אותו מודל.")
    vectors = []
    ranked = semantic_search(query, ITEMS, vectors_out=vectors)
    trace = embedding_trace(query, ITEMS, vectors)
    steps.append(f"3. נבדקו {len(ITEMS)} פריטים. Cosine מודד זווית, לא אורך וקטור.")
    steps.append("4. דירוג (גבוה = כיוון דומה):")
    for item in ranked[:3]:
        steps.append(f"   - ציון {item['score']:.2f} — [{item['id']}] {item['question']}")
    best = ranked[0]
    if best["score"] < MIN_SCORE:
        steps.append(
            f"5. הציון הגבוה ביותר {best['score']:.2f} נמוך מהסף {MIN_SCORE:.2f}."
        )
        steps.append("6. אין מקור מספיק קרוב – לא ממציאים תשובה.")
        return {
            "answer": "לא מצאתי מקור מספיק קרוב.",
            "prompt": _prompt_text(query, True, ranked),
            "what_happened": "\n".join(steps),
            "embedding": trace,
            "notice": notice(),
        }

    steps.append(
        f"5. נבחר [{best['id']}] כי הציון {best['score']:.2f} מעל הסף {MIN_SCORE:.2f}."
    )
    steps.append(
        "6. דירוג גבוה = קרבה סמנטית. זה לא מבטיח שהתשובה נכונה עסקית תמיד."
    )
    return {
        "answer": f"{best['answer']}\n\n(מקור: {best['question']})",
        "prompt": _prompt_text(query, True, ranked),
        "what_happened": "\n".join(steps),
        "embedding": trace,
        "notice": notice(),
    }
