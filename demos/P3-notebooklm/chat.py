# chat.py – הדלת לגרפים
# load_data / add_text → begin_review (עצירה) → approve → ask.
# מנהל: notebook_id (מחברת), thread_id (שיחה), ומחזיר תשובה + ציטוטים + trace.

import re
from pathlib import Path

from langgraph.types import Command

import tracelog
from graph import build_chat
from hitl import build_ingest
from llm_client import notice, tracing_status
from source_store import STORE

DATA_DIR = Path(__file__).resolve().parent / "data"

_ingest = build_ingest()
_chat = build_chat()
_state = {"nb": 1, "session": 1, "batch": 0}
_CITE_RE = re.compile(r"\[(S\d+)\]")


def notebook_id() -> str:
    return f"nb-{_state['nb']}"


def thread_id() -> str:
    return f"{notebook_id()}-s{_state['session']}"


def _chat_cfg():
    return {"configurable": {"thread_id": thread_id()}, "recursion_limit": 25}


def _ingest_cfg():
    return {"configurable": {"thread_id": f"ingest-{notebook_id()}-b{_state['batch']}"}}


def reset_notebook() -> None:
    """מחברת חדשה: אינדקס ריק, ושיחה חדשה."""
    STORE.clear(notebook_id())
    _state["nb"] += 1
    _state["session"] = 1
    _state["batch"] = 0


def new_session() -> None:
    """שיחה חדשה באותה מחברת: אותם מקורות, thread_id חדש (בלי זיכרון)."""
    _state["session"] += 1


# ---------- מקורות ----------
def _title_of(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("# ").strip()
    return fallback


def load_data() -> int:
    """טוענת את כל קבצי data/*.md כמקורות במצב pending."""
    count = 0
    for path in sorted(DATA_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        body = "\n".join(l for l in text.splitlines() if not l.startswith("#")).strip()
        STORE.register(notebook_id(), STORE.next_id(notebook_id()), _title_of(text, path.stem), body)
        count += 1
    return count


def add_text(title: str, text: str) -> str:
    """מוסיפה מקור מטקסט שהודבק. גם הוא pending עד אישור."""
    sid = STORE.next_id(notebook_id())
    STORE.register(notebook_id(), sid, (title or "").strip() or f"טקסט {sid}", (text or "").strip())
    return sid


def pending_ids() -> list[str]:
    return [m["id"] for m in STORE.sources(notebook_id()) if m["status"] == "pending"]


def begin_review() -> dict:
    """מפעילה את גרף האישור על כל ה-pending. הוא נעצר ב-interrupt וממתין לנציגה."""
    ids = pending_ids()
    if not ids:
        return {"choices": [], "log": "אין מקורות שממתינים לאישור.", "pending": []}
    _state["batch"] += 1
    result = _ingest.invoke(
        {"notebook_id": notebook_id(), "source_ids": ids, "flags": {}, "approved_ids": [], "log": []}, _ingest_cfg()
    )
    pending = result["__interrupt__"][0].value["pending"]
    choices = [
        (f"{p['id']} · {p['title']}" + (f"  ⚠️ {', '.join(p['flags'])}" if p["flags"] else ""), p["id"]) for p in pending
    ]
    return {"choices": choices, "log": "\n".join(result["log"]) + "\n⏸ הגרף נעצר וממתין לאישור (interrupt).", "pending": pending}


def approve(ids: list[str]) -> dict:
    result = _ingest.invoke(Command(resume=list(ids)), _ingest_cfg())
    return {"log": "\n".join(result["log"])}


def sources_table() -> str:
    icons = {"pending": "⏳ pending", "approved": "✅ approved", "rejected": "⛔ rejected", "indexed": "📚 indexed", "error": "❌ error"}
    rows = ["| מקור | כותרת | hash | סטטוס | פירוט |", "|---|---|---|---|---|"]
    for m in STORE.sources(notebook_id()):
        rows.append(f"| {m['id']} | {m['title']} | `{m['hash']}` | {icons.get(m['status'], m['status'])} | {m['reason'] or '—'} |")
    return "\n".join(rows) if STORE.sources(notebook_id()) else "אין מקורות במחברת."


def indexed_count() -> int:
    return sum(1 for m in STORE.sources(notebook_id()) if m["status"] == "indexed")


# ---------- שיחה ----------
def mermaid() -> str:
    return _chat.get_graph().draw_mermaid()


def ask(question: str, web: bool = False) -> dict:
    tracelog.start()
    state: dict = {}
    inputs = {"question": question, "web": web, "notebook_id": notebook_id()}
    for mode, data in _chat.stream(inputs, config=_chat_cfg(), stream_mode=["updates", "values"]):
        if mode == "values":
            state = data
    messages = state.get("messages", [])
    answer = messages[-1].content if messages else ""
    cited = []
    for sid in dict.fromkeys(_CITE_RE.findall(answer)):
        meta = next((m for m in STORE.sources(notebook_id()) if m["id"] == sid), None)
        cited.append(f"**{sid}** — {meta['title'] if meta else 'לא ידוע'}")
    tracelog.flush(question, notebook_id(), thread_id())
    return {
        "answer": answer,
        "citations": "**ציטוטים:** " + " · ".join(cited) if cited else "**ציטוטים:** אין",
        "cited_ids": list(dict.fromkeys(_CITE_RE.findall(answer))),
        "retrieved": [(c["source_id"], c["n"], round(c["score"], 2)) for c in state.get("chunks", [])],
        "tools_used": state.get("tools_used", []),
        "trace": "\n".join(tracelog.lines()),
        "footer": (
            f"notebook: `{notebook_id()}` · thread_id: `{thread_id()}` · הודעות שמורות: {len(messages)} · "
            f"מקורות מאונדקסים: {indexed_count()} · {tracing_status()}"
        ),
        "notice": notice(),
    }
