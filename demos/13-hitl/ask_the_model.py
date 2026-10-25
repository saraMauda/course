# קובץ 4 – ההרצה
# upload → (עצירה) → approve → index.   ask → (אולי עצירה) → decide.
# כל קריאה ממשיכה אותו thread_id. בלי thread_id אין resume.

from langgraph.types import Command

from graph import build_ingest, build_qa
from llm_client import notice
from prompt import DEFENSE_HITL, DEFENSE_SEPARATION
from tools import INDEX, make_docs, reset_index

_ingest = build_ingest()
_qa = build_qa()
_epoch = 0
_pending_gate = {"on": False}


def _ingest_cfg():
    return {"configurable": {"thread_id": f"ingest-{_epoch}"}}


def _qa_cfg():
    return {"configurable": {"thread_id": f"qa-{_epoch}"}}


def reset() -> None:
    global _epoch
    _epoch += 1
    reset_index()
    _pending_gate["on"] = False


def docs_table(docs: list[dict]) -> str:
    icons = {"pending": "⏳ pending", "approved": "✅ approved", "rejected": "⛔ rejected", "indexed": "📚 indexed", "error": "❌ error"}
    rows = ["| מסמך | כותרת | סימונים | סטטוס | סיבה |", "|---|---|---|---|---|"]
    for d in docs:
        flags = ", ".join(d.get("flags", [])) or "—"
        rows.append(f"| {d['id']} | {d['title']} | {flags} | {icons.get(d['status'], d['status'])} | {d.get('reason', '') or '—'} |")
    return "\n".join(rows)


def upload(variant: str) -> dict:
    reset()
    result = _ingest.invoke({"docs": make_docs(variant), "approved_ids": [], "log": []}, _ingest_cfg())
    pending = result["__interrupt__"][0].value["pending"]
    docs = _ingest.get_state(_ingest_cfg()).values["docs"]
    choices = [(f"{p['id']} · {p['title']}" + (f"  ⚠️ {', '.join(p['flags'])}" if p["flags"] else ""), p["id"]) for p in pending]
    return {
        "choices": choices,
        "table": docs_table(docs),
        "log": "\n".join(result["log"]) + "\n⏸ הגרף נעצר ב-await_approval וממתין לנציגה (interrupt). ה-State שמור לפי thread_id.",
    }


def approve(ids: list[str]) -> dict:
    result = _ingest.invoke(Command(resume=ids), _ingest_cfg())
    return {"table": docs_table(result["docs"]), "log": "\n".join(result["log"]), "indexed": sorted(INDEX)}


def ask(question: str, defenses: list[str]) -> dict:
    separation, hitl = DEFENSE_SEPARATION in defenses, DEFENSE_HITL in defenses
    _pending_gate["on"] = False
    result = _qa.invoke({"question": question, "separation": separation, "hitl": hitl}, _qa_cfg())
    return _qa_view(result, separation, hitl)


def decide(approved: bool) -> dict:
    if not _pending_gate["on"]:
        return {"answer": "", "status": "אין תשובה שממתינה לאישור.", "prompt": "", "steps": ""}
    _pending_gate["on"] = False
    result = _qa.invoke(Command(resume=approved), _qa_cfg())
    return _qa_view(result, None, None)


def _qa_view(result: dict, separation, hitl) -> dict:
    steps = [f"מסמכים באינדקס: {sorted(INDEX) or 'אין'}"]
    if separation is not None:
        steps.append(f"הגנות: הפרדה={'כן' if separation else 'לא'}, HITL={'כן' if hitl else 'לא'}")
    if "__interrupt__" in result:
        _pending_gate["on"] = True
        proposed = result["__interrupt__"][0].value["answer"]
        steps.append("⏸ gate זיהה הבטחת החזר. הגרף נעצר וממתין לנציגה.")
        return {"answer": "", "status": f"⏸ ממתין לאישור נציגה. התשובה המוצעת: «{proposed}»", "prompt": result.get("prompt", ""), "steps": "\n".join(steps), "pending": True}
    steps.append(f"gate: {result['status']}")
    return {"answer": result["final"], "status": result["status"], "prompt": result.get("prompt", ""), "steps": "\n".join(steps), "pending": False}


def llm_notice() -> str:
    return notice()
