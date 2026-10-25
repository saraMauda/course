# source_store.py – הלב של הידע
# ingest → chunk → embed → persist (עם מטא-דאטה) → retrieve.
# לכל מקור: title, hash, status (pending → approved → indexed | error | rejected).
# אחזור: רק מקורות במצב indexed, ורק של המחברת (notebook) הנוכחית.

import hashlib
import re

from llm_client import embed

TOP_K = 3
MIN_SCORE = 0.3  # סף: מתחת לזה מקטע לא נחשב רלוונטי. בלי סף תמיד נשלוף משהו
MAX_ATTEMPTS = 2  # תקרת ניסיונות להטמעה. אחרי זה status=error, לא קריסה


def chunk_text(text: str) -> list[str]:
    """חיתוך: שני משפטים רצופים, וחפיפה של משפט אחד (a b | b c | c d). משפט אחד = מקטע אחד."""
    parts = [p for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p]
    if len(parts) <= 2:
        return [" ".join(parts)] if parts else []
    return [" ".join(parts[i : i + 2]) for i in range(len(parts) - 1)]


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
        self.notebooks: dict[str, dict] = {}

    def _nb(self, notebook_id: str) -> dict:
        return self.notebooks.setdefault(notebook_id, {"sources": {}, "chunks": []})

    def clear(self, notebook_id: str | None = None) -> None:
        if notebook_id is None:
            self.notebooks.clear()
        else:
            self.notebooks.pop(notebook_id, None)

    # ---- ingest ----
    def register(self, notebook_id: str, source_id: str, title: str, text: str) -> dict:
        """רושם מקור במצב pending. עדיין לא נחתך ולא מוטמע."""
        meta = {
            "id": source_id,
            "title": title,
            "text": text,
            "hash": hashlib.sha1(text.encode("utf-8")).hexdigest()[:10],
            "status": "pending",
            "reason": "",
            "chunks": 0,
        }
        self._nb(notebook_id)["sources"][source_id] = meta
        return meta

    def next_id(self, notebook_id: str) -> str:
        return f"S{len(self._nb(notebook_id)['sources']) + 1}"

    def set_status(self, notebook_id: str, source_id: str, status: str, reason: str = "") -> None:
        meta = self._nb(notebook_id)["sources"][source_id]
        meta["status"], meta["reason"] = status, reason

    def index(self, notebook_id: str, source_id: str, embed_fn=embed) -> bool:
        """chunk → embed → persist. עם ניסיון חוזר, ובסוף status=indexed או error."""
        nb = self._nb(notebook_id)
        meta = nb["sources"][source_id]
        pieces = chunk_text(meta["text"])
        last_error = ""
        for _ in range(MAX_ATTEMPTS):
            try:
                vectors = embed_fn(pieces)
                break
            except Exception as exc:  # כישלון כלי ≠ קריסה
                last_error = str(exc)
        else:
            meta["status"], meta["reason"] = "error", f"הטמעה נכשלה: {last_error}"
            return False
        nb["chunks"] = [c for c in nb["chunks"] if c["source_id"] != source_id]
        for i, (piece, vec) in enumerate(zip(pieces, vectors)):
            nb["chunks"].append({"source_id": source_id, "title": meta["title"], "n": i + 1, "text": piece, "vec": vec})
        meta["status"], meta["chunks"], meta["reason"] = "indexed", len(pieces), f"{len(pieces)} מקטעים"
        return True

    # ---- retrieve ----
    def search(self, notebook_id: str, query: str, k: int = TOP_K, min_score: float = MIN_SCORE) -> list[dict]:
        nb = self._nb(notebook_id)
        allowed = {sid for sid, m in nb["sources"].items() if m["status"] == "indexed"}  # רק מאושר ומאונדקס
        pool = [c for c in nb["chunks"] if c["source_id"] in allowed]
        if not pool:
            return []
        qvec = embed([query])[0]
        ranked = [{**c, "score": cosine(qvec, c["vec"])} for c in pool]
        ranked.sort(key=lambda row: row["score"], reverse=True)
        return [{k_: v for k_, v in row.items() if k_ != "vec"} for row in ranked[:k] if row["score"] >= min_score]

    def sources(self, notebook_id: str) -> list[dict]:
        return list(self._nb(notebook_id)["sources"].values())


STORE = SourceStore()
