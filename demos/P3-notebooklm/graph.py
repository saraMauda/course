# graph.py – גרף השיחה
# START → retrieve → agent ↔ tools → guard → END, עם checkpointer.
#   retrieve = Workflow: הקוד שולף תמיד מהמקורות המאושרים של המחברת.
#   agent ↔ tools = Agent: המודל יכול לחפש שוב (search_sources) או ברשת (web_search / scrape_url).
#   guard = בדיקת פלט בקוד: הבטחת החזר לא יוצאת (HITL gate אופציונלי: עוצרים עם interrupt במקום להחליף).

import operator
import re
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

import tracelog
from llm_client import get_model
from prompt import NOTEBOOK_SYSTEM, REFUSAL_GUARD
from source_store import STORE
from tools import TOOLS_BY_NAME, run_search, tools_for

PROMISE_RE = re.compile(r"החזר מאושר|מגיע לך החזר מלא|נחזיר לך את כל|החזר מלא")


class NotebookState(TypedDict):
    messages: Annotated[list, add_messages]   # רק שאלות, בקשות כלים, Observations ותשובות. בלי הקשר RAG (נגד Context Rot)
    question: str
    web: bool                                  # המשתמשת הפעילה הרחבה לאינטרנט?
    notebook_id: str
    chunks: list[dict]                         # מה נשלף בתור הזה (מקטע, מקור, ציון)
    tools_used: Annotated[list[str], operator.add]


def retrieve(state):
    hits = STORE.search(state["notebook_id"], state["question"])
    if hits:
        lines = "; ".join(f"{h['source_id']}#{h['n']} ({h['score']:.2f})" for h in hits)
        tracelog.log("retrieve", f"נשלפו {len(hits)} מקטעים: {lines}")
    else:
        tracelog.log("retrieve", "לא נשלף כלום מעל הסף (או שאין מקורות מאושרים).")
    return {"chunks": hits, "messages": [HumanMessage(content=state["question"])]}


def _context_message(state) -> HumanMessage:
    """ההקשר נבנה לתור הנוכחי בלבד, ולא נשמר בהיסטוריה."""
    hits = state["chunks"]
    if hits:
        blocks = "\n".join(
            f'<source id="{h["source_id"]}" title="{h["title"]}" chunk="{h["n"]}">\n{h["text"]}\n</source>' for h in hits
        )
    else:
        blocks = "(לא נמצאו מקטעים רלוונטיים במקורות שאושרו)"
    return HumanMessage(content=f"מקורות:\n{blocks}\n\nשאלה: {state['question']}")


def agent(state):
    msgs = state["messages"]
    last_h = max(i for i, m in enumerate(msgs) if isinstance(m, HumanMessage))
    history = [
        m for m in msgs[:last_h]
        if isinstance(m, HumanMessage) or (isinstance(m, AIMessage) and not m.tool_calls and m.content)
    ]
    current = msgs[last_h + 1 :]
    model = get_model().bind_tools(tools_for(state.get("web", False)))
    reply = model.invoke([SystemMessage(content=NOTEBOOK_SYSTEM)] + history + [_context_message(state)] + current)
    if getattr(reply, "tool_calls", None):
        for call in reply.tool_calls:
            tracelog.log("agent", f"ביקש כלי {call['name']}({call['args']})")
    else:
        tracelog.log("agent", "תשובה סופית")
    return {"messages": [reply]}


def tools_node(state):
    results, used = [], []
    for call in state["messages"][-1].tool_calls:
        name, args = call["name"], call["args"]
        used.append(name)
        try:
            if name == "search_sources":
                content, hits = run_search(args["query"], state["notebook_id"])
                tracelog.log("tools", f"search_sources → {len(hits)} מקטעים")
            else:
                content = TOOLS_BY_NAME[name].invoke(args)
                tracelog.log("tools", f"{name} → {str(content)[:80]}")
            status = "success"
        except Exception as exc:  # כלי שנכשל חוזר כ-Observation, לא קריסה
            content, status = f"שגיאת כלי: {exc}", "error"
            tracelog.log("tools", f"{name} נכשל: {exc}")
        results.append(ToolMessage(content=content, tool_call_id=call["id"], name=name, status=status))
    return {"messages": results, "tools_used": used}


def should_continue(state):
    return "tools" if getattr(state["messages"][-1], "tool_calls", None) else "guard"


def guard(state):
    last = state["messages"][-1]
    if PROMISE_RE.search(str(last.content)):
        tracelog.log("guard", "זוהתה הבטחת החזר בתשובה. הוחלפה בהודעה בטוחה.")
        return {"messages": [AIMessage(content=REFUSAL_GUARD, id=last.id)]}
    return {}


def build_chat():
    g = StateGraph(NotebookState)
    g.add_node("retrieve", retrieve)
    g.add_node("agent", agent)
    g.add_node("tools", tools_node)
    g.add_node("guard", guard)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "agent")
    g.add_conditional_edges("agent", should_continue, {"tools": "tools", "guard": "guard"})
    g.add_edge("tools", "agent")
    g.add_edge("guard", END)
    return g.compile(checkpointer=InMemorySaver())
