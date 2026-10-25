# קובץ 4 – ההרצה
# מריצות את הגרף עם stream, וכותבות לכל node מה הוא כתב ל-State.

import json

from graph import build_graph
from llm_client import notice
from prompt import STAGE_1, STAGE_3

_graphs: dict = {}
_epoch = 0


def new_conversation() -> None:
    global _epoch
    _epoch += 1


def thread_id() -> str:
    return f"demo-{_epoch}"


def _graph(stage: str):
    if stage not in _graphs:
        _graphs[stage] = build_graph(stage)
    return _graphs[stage]


def mermaid(stage: str) -> str:
    return _graph(stage).get_graph().draw_mermaid()


def _describe(node: str, update: dict) -> list[str]:
    lines = []
    for msg in update.get("messages", []):
        kind = type(msg).__name__
        if kind == "AIMessage" and msg.tool_calls:
            for call in msg.tool_calls:
                args = json.dumps(call["args"], ensure_ascii=False)
                lines.append(f"node `{node}` כתב ל-State: AIMessage שמבקש {call['name']}({args})")
        elif kind == "AIMessage":
            lines.append(f"node `{node}` כתב ל-State: AIMessage עם תשובה סופית")
        elif kind == "ToolMessage":
            tag = "שגיאה" if getattr(msg, "status", "") == "error" else "תוצאה"
            lines.append(f"node `{node}` כתב ל-State: ToolMessage ({tag}): {str(msg.content)[:140]}")
    if update.get("sources"):
        lines.append(f"node `{node}` הוסיף ל-sources: {update['sources']}")
    return lines


def ask(text: str, stage: str) -> dict:
    graph = _graph(stage)
    config = {"recursion_limit": 25}
    if stage == STAGE_3:
        config["configurable"] = {"thread_id": thread_id()}

    steps = ["1. START → agent"]
    path = ["START"]
    state: dict = {}
    n = 2
    # "updates" = מה כל node כתב. "values" = ה-State המלא אחרי כל צעד.
    for mode, data in graph.stream(
        {"messages": [{"role": "user", "content": text}]}, config=config, stream_mode=["updates", "values"]
    ):
        if mode == "values":
            state = data
            continue
        for node, update in data.items():
            path.append(node)
            for line in _describe(node, update):
                steps.append(f"{n}. {line}")
                n += 1
            if node == "agent" and stage != STAGE_1:
                last = update["messages"][-1]
                goes_to = "tools" if getattr(last, "tool_calls", None) else "END"
                steps.append(f"{n}. קשת מותנית `should_continue` → {goes_to}")
                n += 1
            elif node == "agent":
                steps.append(f"{n}. קשת קבועה agent → END")
                n += 1
            elif node == "tools":
                steps.append(f"{n}. קשת קבועה tools → agent")
                n += 1
    path.append("END")

    messages = state.get("messages", [])
    answer = messages[-1].content if messages else ""
    summary = {
        "messages": f"{len(messages)} הודעות",
        **({"sources": state.get("sources", [])} if stage == STAGE_3 else {}),
        **({"thread_id": thread_id()} if stage == STAGE_3 else {}),
    }
    return {
        "answer": answer,
        "path": " → ".join(path),
        "steps": "\n".join(steps),
        "state": json.dumps(summary, ensure_ascii=False, indent=2),
        "notice": notice(),
    }
