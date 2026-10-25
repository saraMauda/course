# קובץ 3 – השליחה למודל
# בלי לולאה: שאלה אחת, תשובה אחת.
# עם ReAct: Thought → Action → אנחנו מריצות → Observation → חוזרות.

from llm_client import complete, notice
from prompt import ACTIONS, SYSTEM_PROMPT, UNSTRUCTURED_QUESTION
from tools import run_action

MAX_STEPS = 4


def _prompt_text(messages) -> str:
    lines = []
    for msg in messages:
        lines.append(f"[{msg.get('role', '')}]")
        if msg.get("content"):
            lines.append(msg["content"])
        lines.append("")
    return "\n".join(lines).strip()


def parse_react(text: str) -> tuple[str, str, str]:
    thought, action, action_input = "", "", ""
    for line in (text or "").splitlines():
        t = line.strip()
        low = t.lower().replace(" ", "")
        if low.startswith("thought:"):
            thought = t.split(":", 1)[1].strip()
        elif low.startswith("actioninput:") or low.startswith("action_input:"):
            action_input = t.split(":", 1)[1].strip()
        elif low.startswith("action:"):
            action = t.split(":", 1)[1].strip()
            action = action.replace("`", "").split("(")[0].strip().lower()
    return thought, action, action_input


def ask(text: str, use_react: bool) -> dict:
    steps = [f"1. המשתמשת שלחה: {text}"]

    if not use_react:
        messages = [
            {"role": "user", "content": f"{UNSTRUCTURED_QUESTION}\n\n{text}"},
        ]
        steps.append(
            f"2. שלחנו למודל רק «{UNSTRUCTURED_QUESTION}» בלי Thought, בלי Action, בלי כלים."
        )
        reply = complete(messages)
        raw = reply.choices[0].message.content or ""
        steps.append("3. המודל ענה ישר, בלי לולאה.")
        steps.append("4. אין Observation – אין נתון מהמאגר.")
        return {
            "answer": raw,
            "prompt": _prompt_text(messages),
            "what_happened": "\n".join(steps),
            "notice": notice(),
        }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    steps.append("2. שלחנו למודל את הפרומפט (Role + ReAct + Few-Shot) + ההודעה.")

    n = 3
    for _ in range(MAX_STEPS):
        reply = complete(messages)
        raw = reply.choices[0].message.content or ""
        thought, action, action_input = parse_react(raw)
        steps.append(f"{n}. המודל כתב Thought: {thought or '(חסר)'}")
        n += 1
        steps.append(f"{n}. המודל ביקש Action: {action or '(חסר)'} ({action_input})")
        n += 1

        if not action:
            steps.append(f"{n}. אין Action בפורמט – עוצרים בלי לקרוס.")
            return {
                "answer": f"המודל לא החזיר Action בפורמט.\n\nמה המודל החזיר:\n{raw}",
                "prompt": _prompt_text(messages),
                "what_happened": "\n".join(steps),
                "notice": notice(),
            }

        if action == "finish":
            steps.append(f"{n}. זו תשובה סופית. אין הרצת כלי.")
            return {
                "answer": action_input or raw,
                "prompt": _prompt_text(messages),
                "what_happened": "\n".join(steps),
                "notice": notice(),
            }

        if action not in ACTIONS:
            steps.append(f"{n}. פעולה לא ברשימה – עוצרים.")
            return {
                "answer": f"המודל ביקש פעולה לא מוכרת: {action}",
                "prompt": _prompt_text(messages),
                "what_happened": "\n".join(steps),
                "notice": notice(),
            }

        result = run_action(action, action_input)
        steps.append(f"{n}. הקוד שלנו הרץ את {action} והחזיר: {result}")
        n += 1
        messages.append({"role": "assistant", "content": raw})
        messages.append({"role": "user", "content": f"Observation: {result}"})
        steps.append(f"{n}. החזרנו Observation למודל.")
        n += 1

    steps.append(f"{n}. הלולאה נעצרה אחרי {MAX_STEPS} צעדים בלי finish.")
    return {
        "answer": "הלולאה נעצרה בלי תשובה סופית.",
        "prompt": _prompt_text(messages),
        "what_happened": "\n".join(steps),
        "notice": notice(),
    }
