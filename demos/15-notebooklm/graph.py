# קובץ 5 – גרף השיחה
# START → retrieve → agent ↔ tools → END, עם checkpointer.
# retrieve = Workflow (הקוד שולף תמיד). agent ↔ tools = Agent (המודל מחליט אם לחפש ברשת).

from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from llm_client import get_model
from prompt import NOTEBOOK_SYSTEM
from source_store import STORE
from tools import TOOLS, TOOLS_BY_NAME


class NotebookState(TypedDict):
    messages: Annotated[list, add_messages]
    question: str
    web: bool            # המשתמשת הפעילה הרחבה לאינטרנט?
    chunks: list[dict]   # מה נשלף בסבב הזה (מקטע, מקור, ציון)


def retrieve(state):
    hits = STORE.search(state["question"])
    if hits:
        blocks = "\n".join(
            f'<source id="{h["source_id"]}" title="{h["title"]}" chunk="{h["n"]}">\n{h["text"]}\n</source>' for h in hits
        )
    else:
        blocks = "(לא נמצאו מקטעים רלוונטיים במקורות שאושרו)"
    prompt = f"מקורות:\n{blocks}\n\nשאלה: {state['question']}"
    slim = [{k: v for k, v in h.items() if k != "vec"} for h in hits]
    return {"chunks": slim, "messages": [HumanMessage(content=prompt)]}


def agent(state):
    model = get_model().bind_tools(TOOLS) if state.get("web") else get_model()
    reply = model.invoke([SystemMessage(content=NOTEBOOK_SYSTEM)] + state["messages"])
    return {"messages": [reply]}


def tools_node(state):
    results = []
    for call in state["messages"][-1].tool_calls:
        try:
            content, status = TOOLS_BY_NAME[call["name"]].invoke(call["args"]), "success"
        except Exception as exc:  # כלי שנכשל חוזר כ-Observation
            content, status = f"שגיאת כלי: {exc}", "error"
        results.append(ToolMessage(content=content, tool_call_id=call["id"], name=call["name"], status=status))
    return {"messages": results}


def should_continue(state):
    return "tools" if getattr(state["messages"][-1], "tool_calls", None) else END


def build_chat():
    g = StateGraph(NotebookState)
    g.add_node("retrieve", retrieve)
    g.add_node("agent", agent)
    g.add_node("tools", tools_node)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "agent")
    g.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    g.add_edge("tools", "agent")
    return g.compile(checkpointer=InMemorySaver())
