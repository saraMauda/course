# קובץ 3 – השליחה למודל
# בלי Skills: בקשה אחת, תשובה אחת.
# עם Skills: קטלוג בתיאור הכלי → המודל מפעיל activate_skill → אנחנו מחזירות את ה-body → המודל עונה לפיו.

import json

from llm_client import complete, notice
from prompt import SYSTEM_PROMPT, build_tool
from skills import catalog, load_skills


def _as_dict(msg) -> dict:
    data = {"role": "assistant", "content": msg.content}
    if msg.tool_calls:
        data["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.function.name, "arguments": call.function.arguments},
            }
            for call in msg.tool_calls
        ]
    return data


def _prompt_text(messages, tools) -> str:
    lines = []
    for msg in messages:
        lines.append(f"[{msg.get('role', '')}]")
        if msg.get("content"):
            lines.append(msg["content"])
        if msg.get("tool_calls"):
            lines.append(json.dumps(msg["tool_calls"], ensure_ascii=False, indent=2))
        lines.append("")
    lines.append("--- הגדרת הכלים ---")
    if tools:
        lines.append(json.dumps(tools, ensure_ascii=False, indent=2))
    else:
        lines.append("לא נשלחו כלים ולא נשלח קטלוג skills.")
    return "\n".join(lines).strip()


def activate_skill(store: dict, name: str) -> str:
    """הכלי בעולם: מחזיר את ה-body של ה-skill. המודל לא נכנס לכאן."""
    skill = store.get(name)
    if not skill:
        return f"לא נמצא skill בשם {name}. זמינים: {', '.join(store)}"
    return f"הופעל skill: {name}\n\nהשתמשי בהנחיות הבאות להמשך המשימה:\n\n{skill['body']}"


def ask(request: str, use_skills: bool) -> dict:
    store = load_skills()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request},
    ]
    tools = [build_tool(catalog(store))] if use_skills else None
    steps = [f"1. המשתמשת ביקשה: {request}"]

    if use_skills:
        total = sum(len(s["body"]) for s in store.values())
        steps.append(
            f"2. Discovery: האפליקציה סרקה את תיקיית skills ומצאה {len(store)}: "
            + ", ".join(store)
        )
        steps.append(
            f"3. שלב 1 – Metadata: נשלחו רק name + description ({len(catalog(store))} תווים). "
            f"ה-body של כל ה-skills ({total} תווים) עוד לא נשלח."
        )
    else:
        steps.append("2. מצב: בלי Skills. אין קטלוג ואין הנחיות מומחה.")

    first = complete(messages, tools)
    msg = first.choices[0].message

    if not getattr(msg, "tool_calls", None):
        if use_skills:
            steps.append("4. המודל לא ביקש skill – הבקשה לא תואמת אף תיאור בקטלוג. ענה מהידע שלו.")
        else:
            steps.append("3. המודל ענה מהידע הכללי שלו, בלי נהלים של החברה.")
        return {
            "answer": msg.content or "",
            "prompt": _prompt_text(messages, tools),
            "what_happened": "\n".join(steps),
            "notice": notice(),
        }

    messages.append(_as_dict(msg))
    call = msg.tool_calls[0]
    name = json.loads(call.function.arguments).get("name", "")
    steps.append(
        f"4. המודל בחר לפי התיאור: activate_skill(name={name!r}) — זו בקשה, לא הרצה."
    )

    result = activate_skill(store, name)
    messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    steps.append(
        f"5. שלב 2 – SKILL.md: הקוד שלנו טען את ה-body של {name} ({len(result)} תווים) "
        "והחזיר אותו למודל. שאר ה-skills נשארו על המדף."
    )

    second = complete(messages, tools)
    steps.append("6. המודל ענה לפי ההנחיות שנטענו (מבנה, כללים, Checklist).")
    return {
        "answer": second.choices[0].message.content or "",
        "prompt": _prompt_text(messages, tools),
        "what_happened": "\n".join(steps),
        "notice": notice(),
    }
