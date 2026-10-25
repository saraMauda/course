# קובץ 4 – Agent: המודל שולט בזרימה
# אותה לולאת ReAct משיעור 03. המודל בוחר את הצעד, הקוד מריץ, Observation חוזרת.
# אין כאן שום נתיב קבוע. כמה צעדים ובאיזה סדר – המודל מחליט.

from prompt import ACTIONS, AGENT_SYSTEM
from tools import run_action
from recorder import Trace

MAX_STEPS = 5


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


def run_agent(text: str, trace: Trace) -> str:
    messages = [
        {"role": "system", "content": AGENT_SYSTEM},
        {"role": "user", "content": text},
    ]
    trace.say("הקוד לא קבע נתיב. שלחנו למודל את הכלים וההודעה, והוא מנהל.")

    for step in range(1, MAX_STEPS + 1):
        raw = trace.llm(f"Agent, צעד {step}", messages)
        thought, action, action_input = parse_react(raw)
        trace.say(f"המודל חשב: {thought or '(חסר)'}")
        trace.say(f"המודל בחר: {action or '(חסר)'} ({action_input})")

        if not action:
            trace.say("אין Action בפורמט. עוצרים.")
            return f"המודל לא החזיר Action בפורמט.\n\n{raw}"
        if action == "finish":
            trace.say("המודל החליט שמספיק. זו התשובה.")
            return action_input or raw
        if action not in ACTIONS:
            trace.say("פעולה שלא ברשימה. עוצרים.")
            return f"המודל ביקש פעולה לא מוכרת: {action}"

        result = run_action(action, action_input)
        trace.say(f"הקוד הריץ {action} והחזיר: {result}")
        messages.append({"role": "assistant", "content": raw})
        messages.append({"role": "user", "content": f"Observation: {result}"})

    trace.say(f"תקרה: {MAX_STEPS} צעדים בלי finish.")
    return "הלולאה נעצרה בלי תשובה סופית."
