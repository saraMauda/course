# קובץ 2 – האחזור (Retrieval)
# Offline: מטמיעות את השאלות פעם אחת ושומרות אינדקס.
# Runtime: מטמיעות את השאילתה, מדרגות לפי cosine, מחזירות top-K.

from catalog import ITEMS
from llm_client import embed

TOP_K = 3
MIN_SCORE = 0.45

_index = None


def cosine(a, b) -> float:
    dot = na = nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / ((na ** 0.5) * (nb ** 0.5))


def build_index() -> list:
    """Offline: embedding רק לשאלות. התשובות נשארות במאגר."""
    global _index
    if _index is None:
        vectors = embed([item["question"] for item in ITEMS])
        _index = list(zip(ITEMS, vectors))
    return _index


def retrieve(query: str, k: int = TOP_K) -> list:
    """Runtime: embedding לשאילתה, דירוג cosine, top-K."""
    index = build_index()
    query_vec = embed(query)[0]
    ranked = [{**item, "score": cosine(query_vec, vec)} for item, vec in index]
    ranked.sort(key=lambda row: row["score"], reverse=True)
    return ranked[:k]
