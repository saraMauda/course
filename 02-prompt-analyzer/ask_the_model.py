# קובץ 3 – השליחה למודל
# בלי מבנה: שאלה חופשית, תשובה חופשית.
# עם Analyzer: פרומפט מובנה → JSON → ולידציה.

import json

from llm_client import complete, notice
from prompt import SYSTEM_PROMPT, UNSTRUCTURED_QUESTION
from schema import parse_output


def _pretty(data) -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return data
    return json.dumps(data, ensure_ascii=False, indent=2)


def _prompt_text(messages) -> str:
    lines = []
    for msg in messages:
        lines.append(f"[{msg.get('role', '')}]")
        if msg.get("content"):
            lines.append(msg["content"])
        lines.append("")
    return "\n".join(lines).strip()


def ask(text: str, use_analyzer: bool) -> dict:
    steps = [f"1. המשתמשת שלחה טקסט: {text}"]

    if not use_analyzer:
        messages = [
            {"role": "user", "content": f"{UNSTRUCTURED_QUESTION}\n\n{text}"},
        ]
        steps.append(
            f"2. שלחנו למודל רק «{UNSTRUCTURED_QUESTION}» בלי Role, בלי Few-Shot, בלי JSON."
        )
        reply = complete(messages)
        raw = reply.choices[0].message.content or ""
        steps.append("3. המודל ענה בטקסט חופשי.")
        steps.append("4. אין JSON לבדוק – אין ולידציה.")
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
    steps.append(
        "2. שלחנו למודל את הפרומפט (Role + Guardrails + Few-Shot + JSON) + הטקסט."
    )

    reply = complete(messages)
    raw = reply.choices[0].message.content or ""
    steps.append("3. המודל החזיר טקסט.")

    parsed, error = parse_output(raw)
    if error:
        steps.append(f"4. הפלט לא היה JSON תקין, או לא עמד בסכימה: {error}")
        steps.append("5. הוולידציה נכשלה – לא קורסים, מחזירים הודעת כשל.")
        return {
            "answer": f"{error}\n\nמה המודל החזיר:\n{raw}",
            "prompt": _prompt_text(messages),
            "what_happened": "\n".join(steps),
            "notice": notice(),
        }

    steps.append("4. הפלט היה JSON תקין.")
    steps.append("5. הוולידציה עברה – כל השדות חוקיים.")
    return {
        "answer": _pretty(parsed),
        "prompt": _prompt_text(messages),
        "what_happened": "\n".join(steps),
        "notice": notice(),
    }
