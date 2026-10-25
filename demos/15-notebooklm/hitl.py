# קובץ 4 – HITL על המקורות
# parse → [interrupt: אישור] → index.   סטטוסים: pending → approved/rejected → indexed.
# אותו מנגנון כמו בשיעור 13. רק מה שאושר נכנס ל-SourceStore.

import operator
import re
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from source_store import STORE

OUTDATED_RE = re.compile(r"\((?:20(?:0\d|1\d|2[0-3]))\)|\b20(?:0\d|1\d|2[0-3])\b")


class IngestState(TypedDict):
    docs: list[dict]
    log: Annotated[list[str], operator.add]


def parse(state):
    docs = []
    for d in state["docs"]:
        flags = ["ייתכן לא עדכני"] if OUTDATED_RE.search(d["title"] + " " + d["text"]) else []
        docs.append({**d, "flags": flags, "status": "pending", "reason": ""})
    return {"docs": docs, "log": [f"parse: {len(docs)} מקורות, כולם pending."]}


def await_approval(state):
    pending = [{"id": d["id"], "title": d["title"], "flags": d["flags"]} for d in state["docs"]]
    approved = interrupt({"pending": pending})  # הגרף נעצר כאן עד Command(resume=...)
    docs = []
    for d in state["docs"]:
        if d["id"] in approved:
            docs.append({**d, "status": "approved"})
        else:
            reason = "לא עדכני" if d["flags"] else "נדחה ידנית"
            docs.append({**d, "status": "rejected", "reason": reason})
    return {"docs": docs, "log": [f"await_approval: אושרו {list(approved)}."]}


def index(state):
    docs, log = [], []
    for d in state["docs"]:
        if d["status"] == "approved":
            n = STORE.add_source(d["id"], d["title"], d["text"])
            docs.append({**d, "status": "indexed", "reason": f"{n} מקטעים"})
            log.append(f"index: {d['id']} → {n} מקטעים ב-SourceStore.")
        else:
            docs.append(d)
    return {"docs": docs, "log": log}


def build_ingest():
    g = StateGraph(IngestState)
    g.add_node("parse", parse)
    g.add_node("await_approval", await_approval)
    g.add_node("index", index)
    g.add_edge(START, "parse")
    g.add_edge("parse", "await_approval")
    g.add_edge("await_approval", "index")
    g.add_edge("index", END)
    return g.compile(checkpointer=InMemorySaver())
