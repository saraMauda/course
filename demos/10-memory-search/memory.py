# קובץ 3 – הזיכרון
# אותו create_agent משיעור 09. מוסיפים שני דברים:
#   1. checkpointer + thread_id  → השיחה נשמרת בין הודעות
#   2. SummarizationMiddleware   → כשההיסטוריה גדלה, ישן מתכווץ לסיכום (נגד Context Rot)
# ו-record_context, שרק מתעד כמה הודעות המודל קיבל בכל קריאה.

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, wrap_model_call
from langgraph.checkpoint.memory import InMemorySaver

from llm_client import get_model
from prompt import MODE_NONE, MODE_SUMMARY, MODES, SUMMARY_KEEP, SUMMARY_TRIGGER, SYSTEM_PROMPT
from tools import TOOLS

CALLS: list[dict] = []  # כל קריאה למודל בהודעה הנוכחית: כמה הודעות, כמה תווים, ומה בדיוק

_agents: dict = {}
_epoch = 0


@wrap_model_call
def record_context(request, handler):
    """לא משנה כלום. רושם מה המודל *ראה* בקריאה הזאת."""
    dump = "\n".join(f"[{type(m).__name__}] {m.content}" for m in request.messages)
    CALLS.append({"messages": len(request.messages), "chars": len(dump), "dump": dump})
    return handler(request)


def _build(mode: str):
    middleware = [record_context]
    kwargs = {}
    if mode != MODE_NONE:
        kwargs["checkpointer"] = InMemorySaver()  # lab/dev. בפרודקשן: SQLite / Postgres
    if mode == MODE_SUMMARY:
        middleware.insert(
            0,
            SummarizationMiddleware(
                model=get_model(),
                trigger=("messages", SUMMARY_TRIGGER),
                keep=("messages", SUMMARY_KEEP),
            ),
        )
    return create_agent(
        model=get_model(),
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        middleware=middleware,
        **kwargs,
    )


def thread_id(mode: str) -> str:
    return f"demo-{MODES.index(mode)}-{_epoch}"


def new_conversation() -> None:
    """שיחה חדשה = thread_id חדש. הישן נשאר בזיכרון, אבל אף אחד לא פונה אליו."""
    global _epoch
    _epoch += 1


def run(mode: str, text: str) -> list:
    """שולחת הודעה אחת. במצב עם זיכרון, אותו thread_id = אותה שיחה."""
    if mode not in _agents:
        _agents[mode] = _build(mode)
    CALLS.clear()
    config = {"recursion_limit": 25}
    if mode != MODE_NONE:
        config["configurable"] = {"thread_id": thread_id(mode)}
    result = _agents[mode].invoke({"messages": [{"role": "user", "content": text}]}, config=config)
    return result["messages"]
