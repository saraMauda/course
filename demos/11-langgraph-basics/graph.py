# קובץ 3 – הגרף
# ReAct כגרף, מאפס. אותו ReAct משיעורים 03 ו-09, רק שהזרימה כתובה ונראית.
# State = מה הגרף זוכר. Node = פונקציה שמחזירה *רק מה שהשתנה*. Edge = לאן ממשיכים.

import re
from typing import Annotated, TypedDict

from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from llm_client import get_model
from prompt import STAGE_1, STAGE_2, STAGE_3, SYSTEM_PROMPT
from tools import TOOLS, TOOLS_BY_NAME


def merge_unique(old: list, new: list) -> list:
    """Reducer: sources רק גדל, בלי כפילויות. בלי זה כל node היה דורס את הרשימה."""
    return old + [item for item in new if item not in old]


class MessagesState(TypedDict):  # שלבים 1-2
    messages: Annotated[list, add_messages]


class SourcesState(TypedDict):  # שלב 3: אותו State + שדה sources
    messages: Annotated[list, add_messages]
    sources: Annotated[list[str], merge_unique]


# ---------- Nodes ----------
def make_agent_node(with_tools: bool):
    model = get_model().bind_tools(TOOLS) if with_tools else get_model()

    def agent(state):
        reply = model.invoke([SystemMessage(content=SYSTEM_PROMPT)] + state["messages"])
        return {"messages": [reply]}

    return agent


def _source_labels(name: str, args: dict, content: str) -> list[str]:
    if name == "search_sources":
        return re.findall(r"\[([\w-]+)\]", content)
    if name == "get_account":
        return [f"account:{args.get('customer_id', '').strip()}"]
    return []


def make_tools_node(track_sources: bool):
    def tools(state):
        last = state["messages"][-1]
        results, sources = [], []
        for call in last.tool_calls:
            try:
                content = TOOLS_BY_NAME[call["name"]].invoke(call["args"])
                status = "success"
            except Exception as exc:  # כלי שנכשל חוזר כ-Observation, לא קריסה
                content, status = f"שגיאת כלי: {exc}", "error"
            results.append(ToolMessage(content=content, tool_call_id=call["id"], name=call["name"], status=status))
            sources += _source_labels(call["name"], call["args"], content)
        update = {"messages": results}
        if track_sources:
            update["sources"] = sources
        return update

    return tools


# ---------- Conditional edge ----------
def should_continue(state):
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END


# ---------- Build ----------
def build_graph(stage: str):
    state_type = SourcesState if stage == STAGE_3 else MessagesState
    g = StateGraph(state_type)
    g.add_node("agent", make_agent_node(with_tools=stage != STAGE_1))
    g.add_edge(START, "agent")
    if stage != STAGE_1:
        g.add_node("tools", make_tools_node(track_sources=stage == STAGE_3))
        g.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
        g.add_edge("tools", "agent")
    else:
        g.add_edge("agent", END)
    checkpointer = InMemorySaver() if stage == STAGE_3 else None
    return g.compile(checkpointer=checkpointer)
