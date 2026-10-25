# קובץ 3 – ה-Harness
# Agent = Model + Harness. כאן ה-Harness.
# את הלולאה (מודל → כלי → Observation → מודל) כתבנו ידנית בשיעורים 03 ו-08.
# `create_agent` עושה אותה במקומנו. אנחנו מגדירים רק: מודל, כלים, הוראות, בקרה.

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage

from llm_client import get_model
from prompt import SYSTEM_PROMPT
from tools import TOOLS

MAX_ITERATIONS = 8  # תקרה ללולאה. בלי זה סוכן שתקוע רץ לנצח (נספר כצעדים בגרף, לא רק קריאות)


@wrap_tool_call
def tool_errors_as_observation(request, handler):
    """בקרה: כלי שנכשל לא מפיל את התהליך. השגיאה חוזרת למודל כ-Observation."""
    try:
        return handler(request)
    except Exception as exc:
        return ToolMessage(
            content=f"שגיאת כלי ({request.tool_call['name']}): {exc}",
            tool_call_id=request.tool_call["id"],
            status="error",
        )


def build_agent():
    return create_agent(
        model=get_model(),
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        middleware=[tool_errors_as_observation],
    )


def run(agent, text: str) -> list:
    """מריץ את הלולאה ומחזיר את כל ההודעות (שאלה, בקשות כלים, Observations, תשובה)."""
    result = agent.invoke(
        {"messages": [{"role": "user", "content": text}]},
        config={"recursion_limit": MAX_ITERATIONS * 2 + 1},
    )
    return result["messages"]
