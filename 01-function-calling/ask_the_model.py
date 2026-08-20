# קובץ 3 – השליחה למודל
# בלי כלים: שאלה אחת, תשובה אחת.
# עם כלי: המודל מבקש → אנחנו מריצות → המודל מנסח תשובה.

import json

from llm_client import complete, notice
from prompt import SYSTEM_PROMPT, WEATHER_TOOL
from weather_tool import get_weather


def _as_dict(msg) -> dict:
    data = {"role": "assistant", "content": msg.content}
    if msg.tool_calls:
        data["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
            }
            for call in msg.tool_calls
        ]
    return data


def _pretty(data) -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return data
    return json.dumps(data, ensure_ascii=False, indent=2)


def _prompt_text(messages, tools) -> str:
    lines = []
    for msg in messages:
        role = msg.get("role", "")
        lines.append(f"[{role}]")
        if msg.get("content"):
            lines.append(msg["content"])
        if msg.get("tool_calls"):
            lines.append(_pretty(msg["tool_calls"]))
        lines.append("")
    lines.append("--- הגדרת הכלים ---")
    if tools:
        lines.append(_pretty(tools))
    else:
        lines.append("לא נשלחו כלים.")
    return "\n".join(lines).strip()


def ask(question: str, use_tools: bool) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    tools = [WEATHER_TOOL] if use_tools else None
    steps = [
        f"1. המשתמשת שאלה: {question}",
        "2. שלחנו למודל את הפרומפט (system) + השאלה."
        + (" + הגדרת הכלי get_weather." if use_tools else " בלי כלים."),
    ]

    first = complete(messages, tools)
    msg = first.choices[0].message

    if not getattr(msg, "tool_calls", None):
        steps.append("3. המודל ענה ישר, בלי לבקש כלי.")
        steps.append("4. אין הרצת פונקציה – אין נתון חי.")
        return {
            "answer": msg.content or "",
            "prompt": _prompt_text(messages, tools),
            "what_happened": "\n".join(steps),
            "notice": notice(),
        }

    messages.append(_as_dict(msg))
    call = msg.tool_calls[0]
    steps.append(
        f"3. המודל ביקש להריץ: {call.function.name}({call.function.arguments})"
        " — זו בקשה, לא הרצה."
    )

    result = get_weather(**json.loads(call.function.arguments))
    messages.append(
        {"role": "tool", "tool_call_id": call.id, "content": result}
    )
    steps.append(f"4. הקוד שלנו הרץ את get_weather והחזיר:\n{_pretty(result)}")
    steps.append("5. החזרנו למודל את התוצאה האמיתית.")

    second = complete(messages, tools)
    steps.append("6. המודל ניסח תשובה למשתמשת מהנתון, לא מהזיכרון.")

    return {
        "answer": second.choices[0].message.content or "",
        "prompt": _prompt_text(messages, tools),
        "what_happened": "\n".join(steps),
        "notice": notice(),
    }
