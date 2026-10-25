# קובץ 5 – Workflows: הקוד שולט בזרימה
# שלוש תבניות מהמאמר של Anthropic. בכולן **הקוד** קובע את הנתיב.
# המודל נקרא לצעדים מוגדרים: לסווג, לסכם, לנסח, לבדוק.
# (Orchestrator–Workers: מסבירים בקול. כאן לא מומש.)

import json
from concurrent.futures import ThreadPoolExecutor

from prompt import (
    AGGREGATOR_SYSTEM,
    COMPOSER_SYSTEM,
    EVALUATOR_SYSTEM,
    GENERATOR_SYSTEM,
    MAX_ROUNDS,
    NO_ID,
    OUT_OF_SCOPE,
    ROUTER_SYSTEM,
    ROUTES,
    WORKER_SYSTEM,
)
from tools import (
    extract_account_id,
    extract_order_id,
    guess_policy_topic,
    lookup_account,
    lookup_order,
    lookup_policy,
)
from recorder import Trace


def _sys(system: str, user: str) -> list[dict]:
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _context(lines: list[str]) -> str:
    return "\n".join(lines)


# ---------- 1. Routing ----------
def run_routing(text: str, trace: Trace) -> str:
    trace.say("הקוד שלח למודל שאלה אחת בלבד: לאיזה מסלול זה שייך?")
    raw = trace.llm("Router", _sys(ROUTER_SYSTEM, text)).lower()
    route = next((name for name in ROUTES if name in raw), "other")
    trace.say(f"המודל סיווג: {route}. מכאן הקוד ממשיך לבד.")

    if route == "other":
        trace.say("מסלול «מחוץ לתחום»: הקוד עונה תשובה קבועה. אין עוד קריאה למודל.")
        return OUT_OF_SCOPE

    if route == "account":
        acc = extract_account_id(text)
        if not acc:
            trace.say("מסלול «חשבון», אבל אין מספר לקוח. הקוד מבקש אותו. בלי מודל.")
            return NO_ID
        lines = [f"account: {lookup_account(acc)}"]
        trace.say(f"הקוד שלף חשבון {acc}.")
        topic = guess_policy_topic(text)
        if topic:
            lines.append(f"policy: {lookup_policy(topic)}")
            trace.say(f"הקוד שלף מדיניות «{topic}».")
    else:
        order = extract_order_id(text)
        if not order:
            trace.say("מסלול «הזמנה», אבל אין מספר הזמנה. הקוד מבקש אותו. בלי מודל.")
            return NO_ID
        lines = [f"order: {lookup_order(order)}"]
        trace.say(f"הקוד שלף הזמנה {order}.")

    trace.say("המודל רק מנסח תשובה מהנתונים שהקוד כבר הביא.")
    return trace.llm("Composer", _sys(COMPOSER_SYSTEM, f"שאלה: {text}\n\nנתונים:\n{_context(lines)}"))


# ---------- 2. Parallelization ----------
def _sources(text: str) -> list[tuple[str, str]]:
    """שלושה מקורות עצמאיים. כל אחד מחזיר נתונים או None."""
    acc, order, topic = extract_account_id(text), extract_order_id(text), guess_policy_topic(text)
    return [
        ("חשבון", lookup_account(acc) if acc else ""),
        ("מדיניות", lookup_policy(topic) if topic else ""),
        ("הזמנות", lookup_order(order) if order else ""),
    ]


def run_parallel(text: str, trace: Trace) -> str:
    sources = _sources(text)
    trace.say("הקוד הפעיל שלוש חוקרות באותו זמן (חשבון, מדיניות, הזמנות). כל אחת מקור אחר.")

    def worker(item: tuple[str, str]) -> tuple[str, str]:
        name, data = item
        user = f"מקור: {name}\nשאלה: {text}\nנתונים:\n{data or 'אין נתונים'}"
        return name, trace.llm(f"Worker – {name}", _sys(WORKER_SYSTEM, user))

    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(worker, sources))

    for name, summary in results:
        trace.say(f"חוקרת «{name}» החזירה: {summary}")

    trace.say("מאחד: מודל אחד ממזג את הסיכומים לתשובה אחת.")
    lines = "\n".join(f"- {name} → {summary}" for name, summary in results)
    return trace.llm("Aggregator", _sys(AGGREGATOR_SYSTEM, f"שאלה: {text}\n\nסיכומי החוקרות:\n{lines}"))


# ---------- 3. Evaluator–Optimizer ----------
def _parse_verdict(raw: str) -> tuple[bool, str]:
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end > start:
        try:
            data = json.loads(raw[start : end + 1])
            return bool(data.get("pass")), str(data.get("feedback", ""))
        except ValueError:
            pass
    return False, raw.strip() or "תשובת המעריכה לא ברורה."


def run_eval_loop(text: str, trace: Trace) -> str:
    lines = []
    acc, order, topic = extract_account_id(text), extract_order_id(text), guess_policy_topic(text)
    if acc:
        lines.append(f"account: {lookup_account(acc)}")
    if topic and acc:
        lines.append(f"policy: {lookup_policy(topic)}")
    if order:
        lines.append(f"order: {lookup_order(order)}")
    if not lines:
        trace.say("הקוד לא מצא מספר לקוח או הזמנה. אין מה לכתוב ואין מה לבדוק. בלי מודל.")
        return NO_ID if any(w in text for w in ("חויב", "חיוב", "הזמנה", "משלוח")) else OUT_OF_SCOPE
    trace.say("הקוד שלף את הנתונים. מכאן לולאה: כותבים, בודקים, מתקנים.")

    context = _context(lines)
    messages = _sys(GENERATOR_SYSTEM, f"שאלה: {text}\n\nנתונים:\n{context}")
    draft = ""
    for round_no in range(1, MAX_ROUNDS + 1):
        draft = trace.llm(f"Generator, סבב {round_no}", messages)
        trace.say(f"סבב {round_no}. הטיוטה: {draft}")
        raw = trace.llm(f"Evaluator, סבב {round_no}", _sys(EVALUATOR_SYSTEM, f"נתונים:\n{context}\n\nטיוטה:\n{draft}"))
        ok, feedback = _parse_verdict(raw)
        if ok:
            trace.say(f"המעריכה: עבר. יוצאים מהלולאה אחרי {round_no} סבבים.")
            return draft
        trace.say(f"המעריכה: נכשל. משוב: {feedback}")
        messages = messages + [
            {"role": "assistant", "content": draft},
            {"role": "user", "content": f"משוב מהמעריך: {feedback}\nתקני ושלחי טיוטה חדשה."},
        ]
    trace.say(f"תקרה: {MAX_ROUNDS} סבבים בלי אישור. מחזירים את הטיוטה האחרונה.")
    return draft
