# קובץ 6 – chat.py: הדלת לגרפים
# upload → approve → ask. מעבירים thread_id, ומחזירים תשובה + ציטוטים + «מה קרה» (trace מקומי).

import json
import re

from langgraph.types import Command

from graph import build_chat
from hitl import build_ingest
from llm_client import notice
from prompt import SOURCES
from source_store import STORE

_ingest = build_ingest()
_chat = build_chat()
_epoch = 0
_CITE_RE = re.compile(r"\[(S\d+)\]")


def _ingest_cfg():
    return {"configurable": {"thread_id": f"ingest-{_epoch}"}}


def _chat_cfg():
    return {"configurable": {"thread_id": f"notebook-{_epoch}"}, "recursion_limit": 25}


def reset() -> None:
    """מחברת חדשה: אינדקס ריק ו-thread_id חדש."""
    global _epoch
    _epoch += 1
    STORE.clear()


def mermaid() -> str:
    return _chat.get_graph().draw_mermaid()


def sources_table(docs: list[dict]) -> str:
    icons = {"pending": "⏳ pending", "approved": "✅ approved", "rejected": "⛔ rejected", "indexed": "📚 indexed", "error": "❌ error"}
    rows = ["| מקור | כותרת | סימונים | סטטוס | פירוט |", "|---|---|---|---|---|"]
    for d in docs:
        flags = ", ".join(d.get("flags", [])) or "—"
        rows.append(f"| {d['id']} | {d['title']} | {flags} | {icons.get(d['status'], d['status'])} | {d.get('reason') or '—'} |")
    return "\n".join(rows)


def upload() -> dict:
    reset()
    result = _ingest.invoke({"docs": SOURCES, "log": []}, _ingest_cfg())
    pending = result["__interrupt__"][0].value["pending"]
    docs = _ingest.get_state(_ingest_cfg()).values["docs"]
    choices = [(f"{p['id']} · {p['title']}" + (f"  ⚠️ {', '.join(p['flags'])}" if p["flags"] else ""), p["id"]) for p in pending]
    return {"choices": choices, "table": sources_table(docs), "log": "\n".join(result["log"]) + "\n⏸ הגרף נעצר וממתין לאישור (interrupt)."}


def approve(ids: list[str]) -> dict:
    result = _ingest.invoke(Command(resume=ids), _ingest_cfg())
    return {"table": sources_table(result["docs"]), "log": "\n".join(result["log"])}


def ask(question: str, web: bool) -> dict:
    steps, state = [], {}
    inputs = {"question": question, "web": web}
    for mode, data in _chat.stream(inputs, config=_chat_cfg(), stream_mode=["updates", "values"]):
        if mode == "values":
            state = data
            continue
        for node, update in data.items():
            if node == "retrieve":
                chunks = update["chunks"]
                if chunks:
                    lines = "; ".join(f"{c['source_id']}#{c['n']} ({c['score']:.2f})" for c in chunks)
                    steps.append(f"retrieve: נשלפו {len(chunks)} מקטעים: {lines}")
                else:
                    steps.append("retrieve: לא נשלף כלום מעל הסף (או שאין מקורות מאושרים).")
            elif node == "agent":
                msg = update["messages"][-1]
                if getattr(msg, "tool_calls", None):
                    for call in msg.tool_calls:
                        steps.append(f"agent ביקש כלי: {call['name']}({json.dumps(call['args'], ensure_ascii=False)})")
                    steps.append("קשת מותנית → tools")
                else:
                    steps.append("agent: תשובה סופית. קשת מותנית → END")
            elif node == "tools":
                for msg in update["messages"]:
                    steps.append(f"tools: {str(msg.content)[:120]}")
    messages = state.get("messages", [])
    answer = messages[-1].content if messages else ""
    cited = []
    for sid in dict.fromkeys(_CITE_RE.findall(answer)):
        meta = STORE.sources.get(sid)
        cited.append(f"**{sid}** — {meta['title'] if meta else 'לא ידוע'}")
    footer = f"thread_id: `notebook-{_epoch}` · הודעות שמורות: {len(messages)} · מקורות באינדקס: {sorted(STORE.sources) or 'אין'}"
    return {
        "answer": answer,
        "citations": "**ציטוטים:** " + " · ".join(cited) if cited else "**ציטוטים:** אין",
        "steps": "\n".join(steps),
        "footer": footer,
        "notice": notice(),
    }
