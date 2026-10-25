# קובץ 2 – SourceStore
# הלב של הידע: ingest, chunk, embed, persist, retrieve.
# מחזיק רק מקורות שאושרו (HITL). מה שנדחה לא נכנס, ולכן אי אפשר לשלוף אותו.

import re

from llm_client import embed

TOP_K = 3
MIN_SCORE = 0.3  # סף: מתחת לזה מקטע לא נחשב רלוונטי. בלי סף תמיד נשלוף משהו


def chunk_text(text: str) -> list[str]:
    """אסטרטגיית חיתוך פשוטה: משפט למקטע. כך הציטוט מדויק."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]


def cosine(a, b) -> float:
    dot = na = nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / ((na ** 0.5) * (nb ** 0.5))


class SourceStore:
    def __init__(self) -> None:
        self.sources: dict[str, dict] = {}
        self.chunks: list[dict] = []

    def clear(self) -> None:
        self.sources.clear()
        self.chunks.clear()

    def add_source(self, source_id: str, title: str, text: str) -> int:
        """chunk → embed → persist (עם מטא-דאטה). מחזיר כמה מקטעים נוצרו."""
        pieces = chunk_text(text)
        vectors = embed(pieces)
        for i, (piece, vec) in enumerate(zip(pieces, vectors)):
            self.chunks.append({"source_id": source_id, "title": title, "n": i + 1, "text": piece, "vec": vec})
        self.sources[source_id] = {"title": title, "chunks": len(pieces)}
        return len(pieces)

    def search(self, query: str, k: int = TOP_K, min_score: float = MIN_SCORE) -> list[dict]:
        if not self.chunks:
            return []
        qvec = embed([query])[0]
        ranked = [{**c, "score": cosine(qvec, c["vec"])} for c in self.chunks]
        ranked.sort(key=lambda row: row["score"], reverse=True)
        return [row for row in ranked[:k] if row["score"] >= min_score]


STORE = SourceStore()
