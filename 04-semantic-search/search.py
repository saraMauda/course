# קובץ 2 – שתי דרכים לחפש
# מילולי: מחרוזת בתוך שאלה/תשובה. סמנטי: embedding + cosine.

from llm_client import embed

MIN_SCORE = 0.45

STOP = {
    "איך", "מה", "למה", "לי", "את", "של", "על", "עם", "זה", "אם",
    "יש", "או", "לא", "כן", "גם", "רק", "כל", "האם", "אחרי", "לפני",
    "שלי", "אני", "אותי", "בבקשה", "תודה", "היה", "להיות",
}


def _words(text: str) -> list[str]:
    cleaned = (text or "").lower()
    for ch in "?,!.;:\"'()":
        cleaned = cleaned.replace(ch, " ")
    return [w for w in cleaned.split() if len(w) >= 3 and w not in STOP]


def cosine(a, b) -> float:
    dot = na = nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / ((na ** 0.5) * (nb ** 0.5))


def keyword_search(query: str, items: list) -> list:
    """התאמת מחרוזות בלבד. אין embedding."""
    needle = (query or "").strip().lower()
    words = _words(query)
    found = []
    for item in items:
        haystack = f"{item['question']} {item['answer']}".lower()
        if needle and needle in haystack:
            found.append({**item, "score": None, "matched": words, "n": len(words) or 1})
            continue
        matched = [w for w in words if w in haystack]
        if matched:
            found.append({**item, "score": None, "matched": matched, "n": len(matched)})
    found.sort(key=lambda row: row["n"], reverse=True)
    return found


def semantic_search(query: str, items: list) -> list:
    """embedding לשאילתה ולכל פריט, דירוג לפי זווית (cosine)."""
    texts = [query] + [f"{item['question']} {item['answer']}" for item in items]
    vectors = embed(texts)
    ranked = []
    for item, vec in zip(items, vectors[1:]):
        ranked.append({**item, "score": cosine(vectors[0], vec)})
    ranked.sort(key=lambda row: row["score"], reverse=True)
    return ranked
