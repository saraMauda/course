# תשתית חיבור למודל – לא חובה להראות בכיתה.
# OpenAI, ואם נחסם (למשל רימון) עובר ל-Gemini או להדגמה מקומית.

import json
import os
import re
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, AuthenticationError, OpenAI

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

_client = None
_model = ""
_notice = ""


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or default).strip().strip('"').strip("'")


def model_name() -> str:
    return _model or _env("OPENAI_MODEL", "gpt-4o-mini")


def notice() -> str:
    return _notice


def _make(provider: str):
    if provider == "mock":
        return "mock", "demo-local"
    if provider == "gemini":
        key = _env("GEMINI_API_KEY") or _env("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("חסר GEMINI_API_KEY ב-.env")
        model = _env("GEMINI_MODEL") or "gemini-2.0-flash"
        return OpenAI(api_key=key, base_url=GEMINI_URL, timeout=20.0), model
    key = _env("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("חסר OPENAI_API_KEY ב-.env")
    kwargs = {"api_key": key, "timeout": 20.0}
    if _env("OPENAI_BASE_URL"):
        kwargs["base_url"] = _env("OPENAI_BASE_URL")
    return OpenAI(**kwargs), _env("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini"


def _reachable(url: str) -> bool:
    try:
        import httpx

        httpx.get(url, timeout=5.0)
        return True
    except Exception:
        return False


def _connect() -> None:
    global _client, _model, _notice
    wanted = (_env("LLM_PROVIDER", "auto") or "auto").lower()
    if wanted in {"mock", "demo", "offline"}:
        _client, _model = _make("mock")
        _notice = "מצב הדגמה מקומי – בלי אינטרנט."
        return
    if wanted == "gemini":
        _client, _model = _make("gemini")
        return
    if wanted == "auto":
        openai_ok = bool(_env("OPENAI_API_KEY")) and _reachable(
            "https://api.openai.com/v1/models"
        )
        gemini_ok = bool(_env("GEMINI_API_KEY") or _env("GOOGLE_API_KEY")) and _reachable(
            "https://generativelanguage.googleapis.com"
        )
        if openai_ok:
            _client, _model = _make("openai")
        elif gemini_ok:
            _client, _model = _make("gemini")
            _notice = "OpenAI נחסם. עובדים עם Gemini."
        else:
            _client, _model = _make("mock")
            _notice = "אין חיבור למודל. רצות בהדגמה מקומית."
        return
    _client, _model = _make("openai")


def _fake_reply(content=None, tool_calls=None):
    calls = None
    if tool_calls:
        calls = [
            SimpleNamespace(
                id=item["id"],
                function=SimpleNamespace(name=item["name"], arguments=item["arguments"]),
            )
            for item in tool_calls
        ]
    message = SimpleNamespace(content=content, tool_calls=calls)
    usage = SimpleNamespace(prompt_tokens=100, completion_tokens=40, total_tokens=140)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)



# ---- הדגמה מקומית (mock) ----
# בלי אינטרנט כל תפקיד (ROUTER, AGENT, COMPOSER...) מקבל תשובה מדומה.
# המדומה קורא את הנתונים מההודעה (note / amount / eta), לא מכיר תחום מסוים.

_ORDER_WORDS = ("הזמנה", "משלוח", "שליח", "השאלה")
_ACCOUNT_WORDS = ("חויב", "חיוב", "חשבון", "החזר", "קנס", "לקוח", "מנוי")
_ACC_RE = re.compile(r"(?:לקוח|מנוי|חבר)\s*(?:מספר\s*)?(\d+)")
_ORD_RE = re.compile(r"(?:הזמנה|השאלה|בקשה)\s*(?:מספר\s*)?(\d+)")


def _tag(messages) -> str:
    for msg in messages:
        if msg.get("role") == "system":
            return (msg.get("content") or "").strip().splitlines()[0]
    return ""


def _last_user(messages) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content") or ""
    return ""


def _first_user(messages) -> str:
    for msg in messages:
        if msg.get("role") == "user":
            return msg.get("content") or ""
    return ""


def _facts(text: str) -> list[dict]:
    found = []
    for line in (text or "").splitlines():
        if "{" in line:
            try:
                found.append(json.loads(line[line.index("{"):]))
            except ValueError:
                pass
    return found


def _answer_from(facts: list[dict]) -> str:
    valid = [f for f in facts if not f.get("error")]
    if not valid:
        return "לא מצאתי נתונים במערכת. אפשר לוודא את המספר?"
    eligible = any(f.get("refund_eligible") for f in valid)
    parts = []
    for f in valid:
        if "note" in f:
            parts.append(f"בדקתי: {f['note']}")
        if f.get("amount"):
            parts.append(f"הסכום: {f['amount']}.")
        if "policy" in f and eligible:
            parts.append(f["policy"])
    if eligible:
        parts.append("זה יאושר רק אחרי אימות.")
    return " ".join(parts)


def _key_fact(facts: list[dict]) -> str:
    for f in facts:
        if f.get("amount"):
            return str(f["amount"])
        if f.get("eta"):
            return str(f["eta"])
    return ""


def _react(thought: str, action: str, action_input: str):
    return _fake_reply(f"Thought: {thought}\nAction: {action}\nActionInput: {action_input}")


def _mock_agent(messages):
    question = _first_user(messages)
    obs = [m["content"] for m in messages if (m.get("content") or "").startswith("Observation:")]
    acc, order = _ACC_RE.search(question), _ORD_RE.search(question)
    if order:
        if not obs:
            return _react("צריך סטטוס הזמנה.", "lookup_order", order.group(1))
        return _react("יש סטטוס. אפשר לענות.", "finish", _answer_from(_facts(obs[-1][len("Observation:"):])))
    if acc:
        if not obs:
            return _react("צריך לראות את החשבון לפני תשובה.", "lookup_account", acc.group(1))
        if len(obs) == 1:
            # המדומה מנחש נושא מדיניות מהמילים בשאלה (מודל אמיתי בוחר לבד)
            topic = "חיוב כפול" if any(w in question for w in ("פעמיים", "כפול")) else ("איחור" if any(w in question for w in ("איחור", "קנס")) else question)
            return _react("יש נתונים. בודקת מדיניות.", "lookup_policy", topic)
        facts = [f for o in obs for f in _facts(o[len("Observation:"):])]
        return _react("יש חשבון ומדיניות. אפשר לענות.", "finish", _answer_from(facts))
    if any(w in question for w in _ORDER_WORDS + _ACCOUNT_WORDS):
        return _react("חסר מספר. אין מה לשלוף.", "finish", "אפשר מספר לקוח או מספר הזמנה, כדי שאבדוק?")
    return _react("זה לא התחום שלי.", "finish", "אני עוזרת רק בחיובים ובהזמנות, לא בנושא הזה.")


def _mock_router(messages):
    text = _last_user(messages)
    if any(w in text for w in _ORDER_WORDS):
        return _fake_reply("order")
    if any(w in text for w in _ACCOUNT_WORDS):
        return _fake_reply("account")
    return _fake_reply("other")


def _mock_worker(messages):
    text = _last_user(messages)
    facts = [f for f in _facts(text) if not f.get("error")]
    if not facts:
        return _fake_reply("אין מידע.")
    f = facts[0]
    if "policy" in f:
        return _fake_reply(f"מדיניות: {f['policy']}")
    return _fake_reply(f"{f.get('note', '')} {('סכום: ' + str(f['amount'])) if f.get('amount') else ''}".strip())


def _mock_aggregator(messages):
    lines = [l.split("→", 1)[1].strip() for l in _last_user(messages).splitlines() if "→" in l]
    useful = [l for l in lines if l and "אין מידע" not in l]
    if not useful:
        return _fake_reply("לא מצאתי נתונים רלוונטיים בהודעה.")
    return _fake_reply("בדקתי כמה מקורות במקביל. " + " ".join(useful))


def _mock_generator(messages):
    joined = "\n".join(m.get("content") or "" for m in messages)
    if "משוב מהמעריך" not in joined:
        return _fake_reply("מצטערים על אי הנוחות! נטפל בזה מיד ונסדר הכל.")
    return _fake_reply(_answer_from(_facts(_first_user(messages))))


def _mock_evaluator(messages):
    text = _last_user(messages)
    context, _, draft = text.partition("טיוטה:")
    key = _key_fact(_facts(context))
    problems = []
    if key and key not in draft:
        problems.append(f"חסר הנתון המרכזי ({key}).")
    if any(w in draft for w in ("מיד", "מיידי", "כל הכסף")):
        problems.append("יש הבטחה לפני אימות. להסיר.")
    return _fake_reply(json.dumps({"pass": not problems, "feedback": " ".join(problems)}, ensure_ascii=False))


def _mock_composer(messages):
    return _fake_reply(_answer_from(_facts(_last_user(messages))))


_MOCKS = {
    "[AGENT]": _mock_agent,
    "[ROUTER]": _mock_router,
    "[COMPOSER]": _mock_composer,
    "[WORKER]": _mock_worker,
    "[AGGREGATOR]": _mock_aggregator,
    "[GENERATOR]": _mock_generator,
    "[EVALUATOR]": _mock_evaluator,
}


def _mock(messages, tools):
    handler = _MOCKS.get(_tag(messages))
    if handler is None:
        return _fake_reply("(הדגמה מקומית: תפקיד לא מוכר)")
    return handler(messages)


def complete(messages, tools=None):
    global _client, _model, _notice
    if _client is None:
        _connect()

    def call(current):
        if current == "mock":
            return _mock(messages, tools)
        kwargs = {"model": _model, "messages": messages, "temperature": 0}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        return current.chat.completions.create(**kwargs)

    try:
        return call(_client)
    except (APIConnectionError, TimeoutError, OSError):
        if _client != "mock":
            _notice = "אין חיבור למודל. רצות בהדגמה מקומית."
            _client, _model = _make("mock")
            return call("mock")
        raise RuntimeError("אין חיבור למודל.")
    except (AuthenticationError, APIStatusError) as exc:
        raise RuntimeError(f"שגיאת מפתח/הרשאה: {exc}") from exc
