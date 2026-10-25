# hitl.py – אישור מקורות לפני אינדוקס (Human-in-the-Loop אמיתי)
# parse → [interrupt: האם לאשר?] → index.   pending → approved | rejected → indexed | error.
# הגרף נעצר עם interrupt ושומר State ב-checkpointer. ההמשך: Command(resume=...) על אותו thread_id.
# מה שנדחה לא נכנס לאינדקס, ולכן אי אפשר לשלוף אותו.

import operator
import re
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

import tracelog
from source_store import STORE

PII_RE = re.compile(r"\b\d{9}\b|\b0\d{1,2}-\d{7}\b")
OUTDATED_RE = re.compile(r"\((?:20(?:0\d|1\d|2[0-3]))\)|\b20(?:0\d|1\d|2[0-3])\b")
DOMAIN_WORDS = ("חיוב", "החזר", "מנוי", "חשבון", "חבילה", "לקוח")

# סוגי דחייה. הסימונים האוטומטיים הם *מידע לנציגה*, לא החלטה.
REASON_PII = "PII"
REASON_SUSPICIOUS = "הוראה חשודה"
REASON_IRRELEVANT = "לא קשור"
REASON_OUTDATED = "לא עדכני"
REASON_MANUAL = "נדחה ידנית"


def flags_for(title: str, text: str) -> list[str]:
    flags = []
    if PII_RE.search(text):
        flags.append(REASON_PII)
    if "הוראה למערכת" in text or "התעלמ" in text:
        flags.append(REASON_SUSPICIOUS)
    if not any(w in title + " " + text for w in DOMAIN_WORDS):
        flags.append(REASON_IRRELEVANT)
    if OUTDATED_RE.search(title + " " + text):
        flags.append(REASON_OUTDATED)
    return flags


class IngestState(TypedDict):
    notebook_id: str
    source_ids: list[str]
    flags: dict
    approved_ids: list[str]
    log: Annotated[list[str], operator.add]


def parse(state):
    flags = {}
    for sid in state["source_ids"]:
        meta = next(m for m in STORE.sources(state["notebook_id"]) if m["id"] == sid)
        flags[sid] = flags_for(meta["title"], meta["text"])
    flagged = sum(1 for f in flags.values() if f)
    return {"flags": flags, "log": [f"parse: {len(flags)} מקורות, {flagged} עם סימון. כולם pending."]}


def await_approval(state):
    pending = [
        {"id": sid, "title": next(m["title"] for m in STORE.sources(state["notebook_id"]) if m["id"] == sid), "flags": state["flags"][sid]}
        for sid in state["source_ids"]
    ]
    # הגרף נעצר כאן. הערך שחוזר הוא מה שנשלח ב-Command(resume=...).
    # ה-node רץ מחדש מההתחלה בהמשך, ולכן אין כאן תופעות לוואי לפני ה-interrupt.
    approved = interrupt({"pending": pending})
    for sid in state["source_ids"]:
        if sid in approved:
            STORE.set_status(state["notebook_id"], sid, "approved")
        else:
            f = state["flags"][sid]
            reason = f[0] if f else REASON_MANUAL
            STORE.set_status(state["notebook_id"], sid, "rejected", reason)
    return {"approved_ids": list(approved), "log": [f"await_approval: אושרו {list(approved)}."]}


def index(state):
    log = []
    for sid in state["approved_ids"]:
        ok = STORE.index(state["notebook_id"], sid)
        meta = next(m for m in STORE.sources(state["notebook_id"]) if m["id"] == sid)
        log.append(f"index: {sid} → {'indexed, ' + meta['reason'] if ok else 'error, ' + meta['reason']}")
    for sid in state["source_ids"]:
        if sid not in state["approved_ids"]:
            meta = next(m for m in STORE.sources(state["notebook_id"]) if m["id"] == sid)
            log.append(f"index: {sid} לא נכנס לאינדקס (rejected: {meta['reason']}).")
    tracelog.log("hitl", "; ".join(log))
    return {"log": log}


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
