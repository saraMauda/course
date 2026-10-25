# קובץ 3 – הגרף
# Multi-agent כגרף: plan → מומחיות במקביל (Fan-out) → synthesize (Fan-in) → חזרה או סיום.
# התקשורת בין "הסוכנות" היא כתיבה ל-State, לא צ'אט חופשי. לכל מומחית שדה משלה.

import time
from threading import Lock
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from llm_client import get_model
from prompt import (
    ACCOUNT_SYSTEM,
    KB_SYSTEM,
    KB_TOP_K,
    MAX_LOOPS,
    MIN_SOURCES,
    STAGE_1,
    STAGE_3,
    SYNTH_SYSTEM,
    WEB_SYSTEM,
)
from tools import dumps, extract_account_id, kb_search, lookup_account, web_search

RUN_LOG: list[dict] = []  # מתי כל node התחיל והסתיים. מראה מקביליות
LLM_CALLS = [0]  # כמה קריאות למודל בהרצה (עלות)
_lock = Lock()


def merge_unique(old: list, new: list) -> list:
    """Reducer: כמה מומחיות כותבות ל-sources במקביל. בלי זה הכתיבה האחרונה הייתה דורסת."""
    return old + [item for item in new if item not in old]


class ResearchState(TypedDict):
    question: str            # global: נכנס בהתחלה
    plan: list[str]          # global: מי עובדת בסבב הזה (plan כותב)
    attempt: int             # global: מספר הסבב (plan כותב)
    kb_notes: str            # כל מומחית כותבת *רק* לשדה שלה
    account_notes: str
    web_notes: str
    sources: Annotated[list[str], merge_unique]  # global משותף, עם Reducer
    draft_answer: str        # synthesize כותב


def _llm(system: str, user: str) -> str:
    with _lock:
        LLM_CALLS[0] += 1
    reply = get_model().invoke([SystemMessage(content=system), HumanMessage(content=user)])
    return str(reply.content).strip()


def _logged(name):
    """עוטף node ורושם זמני התחלה וסיום."""

    def wrap(fn):
        def inner(state):
            start = time.time()
            try:
                return fn(state)
            finally:
                with _lock:
                    RUN_LOG.append({"node": name, "start": start, "end": time.time()})

        return inner

    return wrap


# ---------- Plan (Orchestrator) ----------
def make_plan_node(dynamic: bool):
    def plan(state):
        attempt = state.get("attempt", 0) + 1
        question = state["question"]
        if dynamic:
            chosen = ["kb"]
            if extract_account_id(question):
                chosen.append("account")
            if any(w in question for w in ("חדשות", "עדכני")):
                chosen.append("web")
        else:
            chosen = ["kb", "account", "web"]
        # מאפסות את ההערות של הסבב הקודם. המקורות (sources) רק מצטברים.
        return {"plan": chosen, "attempt": attempt, "kb_notes": "", "account_notes": "", "web_notes": ""}

    return plan


def route_plan(state):
    """קשת מותנית שמחזירה *רשימה*: LangGraph מריץ את כולן במקביל."""
    return state["plan"]


# ---------- Specialists ----------
@_logged("kb")
def kb_node(state):
    top_k = KB_TOP_K[min(state["attempt"] - 1, len(KB_TOP_K) - 1)]
    hits = kb_search(state["question"], top_k, fuzzy=state["attempt"] > 1)
    data = "\n".join(f"[{h['id']}] {h['text']}" for h in hits)
    notes = _llm(KB_SYSTEM, f"שאלה: {state['question']}\nנתונים:\n{data or 'אין נתונים'}")
    return {"kb_notes": notes, "sources": [h["id"] for h in hits]}


@_logged("account")
def account_node(state):
    acc = extract_account_id(state["question"])
    found = lookup_account(acc) if acc else None
    data = dumps(found) if found else ""
    notes = _llm(ACCOUNT_SYSTEM, f"שאלה: {state['question']}\nנתונים:\n{data or 'אין נתונים'}")
    return {"account_notes": notes, "sources": [f"account:{acc}"] if found else []}


@_logged("web")
def web_node(state):
    try:
        data = web_search(state["question"])
    except Exception as exc:  # מומחית שנכשלה לא מפילה את הגרף. היא כותבת שגיאה, והמאחדת מתמודדת
        return {"web_notes": f"שגיאה: {exc}"}
    notes = _llm(WEB_SYSTEM, f"שאלה: {state['question']}\nנתונים:\n{data or 'אין נתונים'}")
    return {"web_notes": notes, "sources": ["web:example.com"] if data else []}


# ---------- Fan-in ----------
def synthesize(state):
    lines = [f"kb: {state.get('kb_notes', '')}", f"account: {state.get('account_notes', '')}", f"web: {state.get('web_notes', '')}"]
    answer = _llm(SYNTH_SYSTEM, f"שאלה: {state['question']}\n\nסיכומי המומחיות:\n" + "\n".join(lines))
    return {"draft_answer": answer}


def route_after_synth(state):
    """כלל עצירה: חוזרות לתכנון אם אין מספיק מקורות, ועד MAX_LOOPS סבבים נוספים."""
    enough = len(state.get("sources", [])) >= MIN_SOURCES
    rounds_left = state["attempt"] < 1 + MAX_LOOPS
    return END if enough or not rounds_left else "plan"


# ---------- Build ----------
def build_graph(stage: str):
    g = StateGraph(ResearchState)
    g.add_node("plan", make_plan_node(dynamic=stage == STAGE_3))
    g.add_node("kb", kb_node)
    g.add_node("account", account_node)
    g.add_node("web", web_node)
    g.add_node("synthesize", synthesize)
    g.add_edge(START, "plan")

    if stage == STAGE_1:  # סדרתי: אחת אחרי השנייה
        g.add_edge("plan", "kb")
        g.add_edge("kb", "account")
        g.add_edge("account", "web")
        g.add_edge("web", "synthesize")
        g.add_edge("synthesize", END)
        return g.compile()

    if stage == STAGE_3:  # plan בוחרת מי עובדת, ויש לולאה
        g.add_conditional_edges("plan", route_plan, ["kb", "account", "web"])
    else:  # Fan-out קבוע: שלוש במקביל
        for name in ("kb", "account", "web"):
            g.add_edge("plan", name)
    # Fan-in: כולן רצות באותו צעד, ו-synthesize רצה אחרי שכולן סיימו
    for name in ("kb", "account", "web"):
        g.add_edge(name, "synthesize")

    if stage == STAGE_3:
        g.add_conditional_edges("synthesize", route_after_synth, {"plan": "plan", END: END})
    else:
        g.add_edge("synthesize", END)
    return g.compile()
