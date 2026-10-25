# קובץ 4 – ההרצה
# מריצות את הגרף עם stream. לכל node: מה כתב ל-State. ובסוף: ציר זמן, כדי לראות מקביליות.

import json
import time

from graph import LLM_CALLS, RUN_LOG, build_graph
from llm_client import notice
from prompt import STAGE_1

_graphs: dict = {}
PARALLEL_NODES = ("kb", "account", "web")


def _graph(stage: str):
    if stage not in _graphs:
        _graphs[stage] = build_graph(stage)
    return _graphs[stage]


def mermaid(stage: str) -> str:
    return _graph(stage).get_graph().draw_mermaid()


def _short(value, limit: int = 110) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text if len(text) <= limit else text[:limit] + "…"


def _describe(node: str, update: dict) -> str:
    parts = []
    for key, value in update.items():
        if key == "sources":
            parts.append(f"sources += {value}")
        else:
            parts.append(f"{key} = {_short(value)}")
    return f"`{node}` כתב ל-State: " + "; ".join(parts) if parts else f"`{node}` לא כתב כלום"


def _timeline() -> str:
    if not RUN_LOG:
        return ""
    t0 = min(r["start"] for r in RUN_LOG)
    rows = sorted(RUN_LOG, key=lambda r: r["start"])
    lines = [f"{r['node']:<8} {r['start'] - t0:4.2f}s → {r['end'] - t0:4.2f}s" for r in rows]
    return "\n".join(lines)


def _path(nodes: list[str], stage: str) -> str:
    out, group = ["START"], []
    for node in nodes:
        if stage != STAGE_1 and node in PARALLEL_NODES:
            group.append(node)
            continue
        if group:
            out.append("(" + " | ".join(group) + ")" if len(group) > 1 else group[0])
            group = []
        out.append(node)
    if group:
        out.append("(" + " | ".join(group) + ")" if len(group) > 1 else group[0])
    out.append("END")
    return " → ".join(out)


def ask(text: str, stage: str) -> dict:
    graph = _graph(stage)
    RUN_LOG.clear()
    LLM_CALLS[0] = 0
    begin = time.time()

    nodes, steps, state = [], [], {}
    for mode, data in graph.stream({"question": text, "sources": []}, config={"recursion_limit": 40}, stream_mode=["updates", "values"]):
        if mode == "values":
            state = data
            continue
        for node, update in data.items():
            nodes.append(node)
            steps.append(f"{len(steps) + 1}. {_describe(node, update)}")
    elapsed = time.time() - begin

    rounds = state.get("attempt", 1)
    sources = state.get("sources", [])
    summary = (
        f"**זמן ריצה:** {elapsed:.1f} שניות · **קריאות למודל:** {LLM_CALLS[0]} · "
        f"**סבבים:** {rounds} · **מקורות:** {len(sources)}"
    )
    return {
        "answer": state.get("draft_answer", ""),
        "path": f"**המסלול:** {_path(nodes, stage)}",
        "summary": summary,
        "steps": "\n".join(steps),
        "timeline": _timeline(),
        "state": json.dumps({"sources": sources, "attempt": rounds, "plan": state.get("plan", [])}, ensure_ascii=False, indent=2),
        "notice": notice(),
    }
