# tools/search_sources.py – חיפוש מחדש במקורות המאושרים (RAG ככלי)
# ה-retrieve node שולף פעם אחת לפני הסוכן. הכלי הזה מאפשר לסוכן לנסות שוב, עם ניסוח אחר.
# notebook_id לא חשוף למודל: ה-tools node מזריק אותו (המודל לא בוחר מחברת).

from langchain.tools import tool

from source_store import STORE

NOT_FOUND = "לא נמצא במאגר המאושר."


@tool
def search_sources(query: str) -> str:
    """חיפוש סמנטי במקורות שאושרו במחברת. השתמשי כשהמקטעים שקיבלת לא עונים, וכדאי לנסח את השאילתה מחדש."""
    raise RuntimeError("מופעל דרך run_search בלבד (ה-tools node מזריק notebook_id)")


def run_search(query: str, notebook_id: str) -> tuple[str, list[dict]]:
    hits = STORE.search(notebook_id, query)
    if not hits:
        return NOT_FOUND, []
    text = "\n".join(f"[{h['source_id']}#{h['n']}] {h['text']}" for h in hits)
    return text, hits
