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


def semantic_search(query: str, items: list, vectors_out: list | None = None) -> list:
    """embedding לשאילתה ולכל פריט, דירוג לפי זווית (cosine).
    vectors_out (אופציונלי): רשימה שתתמלא בוקטורים, להצגה בחלון."""
    texts = [query] + [f"{item['question']} {item['answer']}" for item in items]
    vectors = embed(texts)
    if vectors_out is not None:
        vectors_out[:] = vectors
    ranked = []
    for item, vec in zip(items, vectors[1:]):
        ranked.append({**item, "score": cosine(vectors[0], vec)})
    ranked.sort(key=lambda row: row["score"], reverse=True)
    return ranked


def _head(vec, n: int = 8) -> str:
    shown = ", ".join(f"{x:.3f}" for x in vec[:n])
    return f"[{shown}, ...]" if len(vec) > n else f"[{shown}]"


def embedding_trace(query: str, items: list, vectors: list, top: int = 3) -> str:
    """טקסט להצגה בחלון: הוקטורים (תחילתם) וחישוב ה-cosine צעד אחר צעד.
    vectors: מה ש-semantic_search מילאה ב-vectors_out (שאילתה ראשונה)."""
    qvec = vectors[0]
    dims = len(qvec)

    lines = [
        f"כל טקסט הפך לוקטור של {dims} מספרים. מוצגים רק 8 הראשונים.",
        "",
        f"שאילתה: {query}",
        f"  וקטור: {_head(qvec)}",
        f"  אורך הוקטור |q| = {sum(x * x for x in qvec) ** 0.5:.3f}",
        "",
        f"חישוב cosine מול {top} הפריטים הקרובים ביותר:",
    ]

    scored = []
    for item, vec in zip(items, vectors[1:]):
        dot = sum(x * y for x, y in zip(qvec, vec))
        nq = sum(x * x for x in qvec) ** 0.5
        nv = sum(y * y for y in vec) ** 0.5
        score = dot / (nq * nv) if nq and nv else 0.0
        scored.append((score, item, vec, dot, nq, nv))
    scored.sort(key=lambda row: row[0], reverse=True)

    for score, item, vec, dot, nq, nv in scored[:top]:
        lines += [
            "",
            f"[{item['id']}] {item['question']}",
            f"  וקטור: {_head(vec)}",
            f"  מכפלה סקלרית (dot) = {dot:.3f}",
            f"  |פריט| = {nv:.3f}",
            f"  cosine = {dot:.3f} / ({nq:.3f} × {nv:.3f}) = {score:.3f}",
        ]
    return "\n".join(lines)
