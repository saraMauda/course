# תשתית חיבור למודל – לא חובה להראות בכיתה.
# OpenAI, ואם נחסם (למשל רימון) עובר ל-Gemini או להדגמה מקומית.

import json
import os
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


def _first_user(messages) -> str:
    for msg in messages:
        content = msg.get("content") or ""
        if msg.get("role") == "user" and not content.startswith("Observation:"):
            return content
    return ""


def _system_text(messages) -> str:
    for msg in messages:
        if msg.get("role") == "system":
            return msg.get("content") or ""
    return ""


def _react(thought: str, action: str, action_input: str) -> object:
    text = (
        f"Thought: {thought}\n"
        f"Action: {action}\n"
        f"ActionInput: {action_input}"
    )
    return _fake_reply(text)


def _mock(messages, tools):
    system = _system_text(messages)
    question = _first_user(messages)
    joined = "\n".join(m.get("content") or "" for m in messages)
    obs = joined.count("Observation:")

    if not system:
        if any(k in question for k in ("מזג", "weather")):
            return _fake_reply("נראה שיהיה חם. זו השערה, בלי בדיקה.")
        if any(k in question for k in ("הזמנה", "משלוח")):
            return _fake_reply(
                "ההזמנה כנראה בדרך ומגיעה מחר. זו תשובה חופשית, בלי מאגר."
            )
        return _fake_reply(
            "לפי מה שאני יודעת מגיע לך החזר מלא מיד, בלי בדיקה. "
            "זו תשובה חופשית – לא ראיתי את החיוב."
        )

    is_order = "lookup_order" in system or "lookup_shipping" in system

    if any(k in question for k in ("מזג", "weather")):
        domain = "הזמנות ומשלוחים" if is_order else "חיובים ומדיניות החברה"
        return _react(
            "זה לא התחום שלי. אין מה לשלוף מהמאגר.",
            "finish",
            f"אני עוזרת רק ב{domain}, לא במזג אוויר.",
        )

    if is_order:
        order_id = "88" if "88" in question else "88"
        if obs == 0:
            return _react("צריך את סטטוס ההזמנה לפני תשובה.", "lookup_order", order_id)
        if obs == 1:
            return _react("יש סטטוס. משלימה פרטי משלוח.", "lookup_shipping", order_id)
        return _react(
            "יש סטטוס ומשלוח. אפשר לענות.",
            "finish",
            "הזמנה 88 במסירה בתל אביב, עד 18:00 היום.",
        )

    customer = "100" if "100" in question else "312"
    if obs == 0:
        return _react("צריך לראות את החיוב לפני תשובה.", "lookup_bill", customer)
    if obs == 1:
        return _react("יש חיוב. בודקת מדיניות.", "lookup_policy", "חיוב כפול")
    if "תעלמ" in question:
        return _react(
            "אסור להתעלם ממדיניות. עונים לפי החיוב שמצאנו.",
            "finish",
            "לא מתעלמים מהמדיניות. אצלך יש שני חיובים זהים על חבילת גלישה ביולי. "
            "מגיע החזר של חיוב אחד תוך 5 ימי עסקים, אחרי האימות.",
        )
    if customer == "100":
        return _react(
            "חיוב אחד בלבד – אין כפל.",
            "finish",
            "בדקתי: ביולי יש חיוב אחד של 39.90 על חבילת גלישה. אין חיוב כפול ואין החזר.",
        )
    return _react(
        "יש כפל חיוב ומדיניות ברורה.",
        "finish",
        "בדקתי את חשבון 312: שני חיובים זהים של 39.90 ביולי על חבילת גלישה. "
        "לפי המדיניות מגיע החזר של חיוב אחד תוך 5 ימי עסקים.",
    )


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
