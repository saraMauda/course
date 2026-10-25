# קובץ 4 – השליחה
# שולחות הודעה, ורואות: תשובה, כמה הקשר המודל קיבל, מה בדיוק קיבל, ומה קרה.

import json

import memory
from llm_client import notice
from memory import CALLS, run
from prompt import MODE_NONE


def ask(text: str, mode: str) -> dict:
    messages = run(mode, text)

    # ההודעות של התור הנוכחי: מהשאלה האחרונה ועד התשובה.
    # אם SUMMARY_KEEP קטן מדי, גם השאלה הנוכחית עלולה להיכנס לסיכום. אז לוקחות את כל מה שנשאר.
    found = [i for i, m in enumerate(messages) if type(m).__name__ == "HumanMessage" and m.content == text]
    turn = messages[found[-1]:] if found else messages

    steps = [f"1. המשתמשת שלחה: {text}"]
    n = 2
    for msg in turn[1:]:
        kind = type(msg).__name__
        if kind == "AIMessage" and msg.tool_calls:
            for call in msg.tool_calls:
                steps.append(f"{n}. המודל ביקש כלי: {call['name']}({json.dumps(call['args'], ensure_ascii=False)})")
                n += 1
        elif kind == "ToolMessage":
            steps.append(f"{n}. ה-Harness הרץ והחזיר: {str(msg.content)[:200]}")
            n += 1
        elif kind == "AIMessage":
            steps.append(f"{n}. המודל ענה.")
            n += 1

    for i, call in enumerate(CALLS, 1):
        steps.append(f"קריאה {i} למודל: קיבל {call['messages']} הודעות ({call['chars']} תווים)")
    summarized = type(messages[0]).__name__ == "HumanMessage" and str(messages[0].content).startswith("Here is a summary")
    if summarized:
        steps.append("הסיכום פעל: ההיסטוריה הישנה הוחלפה בהודעת סיכום אחת.")

    if mode == MODE_NONE:
        state = "אין checkpointer. כל הודעה מגיעה למודל לבד."
    else:
        state = f"thread_id: `{memory.thread_id(mode)}` · הודעות שמורות בשיחה: **{len(messages)}**"
    last = CALLS[-1] if CALLS else {"messages": 0, "chars": 0, "dump": ""}
    context = f"{state} · בקריאה האחרונה המודל קיבל **{last['messages']}** הודעות, **{last['chars']}** תווים"

    answer = messages[-1].content if type(messages[-1]).__name__ == "AIMessage" else ""
    return {
        "answer": answer,
        "context": context,
        "prompt": last["dump"] or "(לא נשלח פרומפט)",
        "what_happened": "\n".join(steps),
        "notice": notice(),
    }
