# קובץ 4 – השליחה
# בלי Harness: מודל לבד, שאלה אחת, תשובה אחת.
# עם LangChain: create_agent מריץ את הלולאה, ואנחנו רק קוראות מה קרה.

import json

from harness import build_agent, run
from llm_client import get_model, notice
from prompt import MODE_AGENT, PLAIN_QUESTION, SYSTEM_PROMPT
from tools import TOOLS


def _tools_text() -> str:
    lines = []
    for t in TOOLS:
        args = ", ".join(t.args)
        lines.append(f"- {t.name}({args}): {t.description}")
    return "\n".join(lines)


def ask(text: str, mode: str) -> dict:
    steps = [f"1. המשתמשת שלחה: {text}"]

    if mode != MODE_AGENT:
        prompt = f"[user]\n{PLAIN_QUESTION}\n\n{text}"
        steps.append("2. שלחנו למודל שאלה אחת, בלי System prompt ובלי כלים.")
        reply = get_model().invoke(f"{PLAIN_QUESTION}\n\n{text}")
        steps.append("3. המודל ענה ישר. אין לולאה, אין Observation, אין נתון מהמאגר.")
        return {
            "answer": reply.content,
            "prompt": prompt,
            "what_happened": "\n".join(steps),
            "notice": notice(),
        }

    prompt = f"[system]\n{SYSTEM_PROMPT}\n\n[tools]\n{_tools_text()}\n\n[user]\n{text}"
    steps.append("2. ה-Harness שלח למודל: System prompt + רשימת הכלים (שם, פרמטרים, תיאור) + ההודעה.")
    try:
        messages = run(build_agent(), text)
    except Exception as exc:
        return {
            "answer": f"הלולאה נעצרה: {exc}",
            "prompt": prompt,
            "what_happened": "\n".join(steps),
            "notice": notice(),
        }

    n, calls = 3, 0
    for msg in messages[1:]:
        kind = type(msg).__name__
        if kind == "AIMessage" and msg.tool_calls:
            for call in msg.tool_calls:
                args = json.dumps(call["args"], ensure_ascii=False)
                steps.append(f"{n}. המודל ביקש כלי: {call['name']}({args})")
                n += 1
        elif kind == "ToolMessage":
            calls += 1
            tag = "נכשל. חזר כ-Observation" if getattr(msg, "status", "") == "error" else "הרץ"
            steps.append(f"{n}. ה-Harness {tag}: {msg.content}")
            n += 1
        elif kind == "AIMessage":
            steps.append(f"{n}. אין בקשת כלי. המודל החזיר תשובה סופית.")
            n += 1
    if calls == 0:
        steps.append(f"{n}. המודל החליט שלא צריך כלי.")

    answer = messages[-1].content if type(messages[-1]).__name__ == "AIMessage" else ""
    return {
        "answer": answer,
        "prompt": prompt,
        "what_happened": "\n".join(steps),
        "notice": notice(),
    }
