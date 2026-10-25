# קובץ 3 – שני גרפים עם נקודות עצירה
# 1. ingest: parse → [interrupt: אישור מקורות] → index          (Upload → Review → Approve → Index)
# 2. qa:     retrieve → answer → [interrupt: הבטחת החזר?]        (הגנה אחרונה על הפלט)
# `interrupt` עוצר את הגרף ושומר State ב-checkpointer. ההמשך: Command(resume=...) על אותו thread_id.

import operator
import re
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from llm_client import get_model
from prompt import ANSWER_SYSTEM, SEPARATION_ADDON
from tools import INDEX, MAX_ATTEMPTS, embed, flags_for

PROMISE_RE = re.compile(r"החזר מאושר|מגיע לך החזר מלא|נחזיר לך את כל|החזר מלא")


# ================= 1. Ingest =================
class IngestState(TypedDict):
    docs: list[dict]           # id, title, text, flags, status, reason
    approved_ids: list[str]    # מה שהנציגה אישרה (העריכה האנושית של ה-State)
    log: Annotated[list[str], operator.add]


def parse(state):
    docs = [{**d, "flags": flags_for(d), "status": "pending", "reason": ""} for d in state["docs"]]
    flagged = sum(1 for d in docs if d["flags"])
    return {"docs": docs, "log": [f"parse: {len(docs)} מסמכים, {flagged} עם סימון. הכל pending."]}


def await_approval(state):
    pending = [{"id": d["id"], "title": d["title"], "flags": d["flags"]} for d in state["docs"]]
    # כאן הגרף נעצר. הערך שיוחזר הוא מה שנשלח ב-Command(resume=...).
    # שימי לב: ה-node רץ מחדש מההתחלה בהמשך, ולכן אין כאן פעולות עם תופעות לוואי לפני ה-interrupt.
    approved_ids = interrupt({"pending": pending})
    docs = []
    for d in state["docs"]:
        if d["id"] in approved_ids:
            docs.append({**d, "status": "approved"})
        else:
            reason = "PII" if "PII" in d["flags"] else "הוראה חשודה" if "הוראה חשודה" in d["flags"] else "לא קשור" if "לא קשור" in d["flags"] else "נדחה ידנית"
            docs.append({**d, "status": "rejected", "reason": reason})
    return {"docs": docs, "approved_ids": list(approved_ids), "log": [f"await_approval: אושרו {list(approved_ids)}."]}


def index(state):
    docs, log = [], []
    for d in state["docs"]:
        if d["status"] != "approved":
            docs.append(d)
            continue
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                embed(d)
                docs.append({**d, "status": "indexed"})
                log.append(f"index: {d['id']} הוטמע (ניסיון {attempt}).")
                break
            except Exception as exc:  # כישלון כלי ≠ קריסה: ניסיון חוזר, ואחרי התקרה סטטוס error
                log.append(f"index: {d['id']} נכשל בניסיון {attempt}: {exc}")
                if attempt == MAX_ATTEMPTS:
                    docs.append({**d, "status": "error", "reason": str(exc)})
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


# ================= 2. Q&A =================
class QAState(TypedDict):
    question: str
    separation: bool
    hitl: bool
    prompt: str
    answer: str
    final: str
    status: str


def retrieve_and_answer(state):
    docs = list(INDEX.values())  # רק מסמכים מאושרים והוטמעו
    if state["separation"]:
        sources = "\n".join(f'<source id="{d["id"]}">\n{d["text"]}\n</source>' for d in docs)
        system = ANSWER_SYSTEM + SEPARATION_ADDON
    else:
        sources = "\n".join(f"מקור {d['id']}:\n{d['text']}" for d in docs)
        system = ANSWER_SYSTEM
    user = f"{sources}\nשאלה: {state['question']}"
    reply = get_model().invoke([SystemMessage(content=system), HumanMessage(content=user)])
    prompt = f"[system]\n{system}\n\n[user]\n{user}"
    return {"prompt": prompt, "answer": str(reply.content).strip()}


def gate(state):
    answer = state["answer"]
    if state["hitl"] and PROMISE_RE.search(answer):
        approved = interrupt({"answer": answer})
        if approved:
            return {"final": answer, "status": "נשלח אחרי אישור נציגה"}
        return {"final": "התשובה נחסמה על ידי הנציגה ולא נשלחה ללקוחה.", "status": "נחסם על ידי נציגה"}
    return {"final": answer, "status": "נשלח אוטומטית"}


def build_qa():
    g = StateGraph(QAState)
    g.add_node("answer", retrieve_and_answer)
    g.add_node("gate", gate)
    g.add_edge(START, "answer")
    g.add_edge("answer", "gate")
    g.add_edge("gate", END)
    return g.compile(checkpointer=InMemorySaver())
