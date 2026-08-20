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


def _mock(messages, tools):
    last = messages[-1]
    role = last.get("role")
    text = last.get("content") or ""

    if role == "tool":
        data = json.loads(text)
        if data.get("error"):
            return _fake_reply("השירות לא היה זמין. אפשר לנסות שוב בעוד כמה דקות.")
        loc = data.get("location", "העיר")
        place = "תל אביב" if "tel" in str(loc).lower() else loc
        return _fake_reply(
            f"ב{place} עכשיו {data.get('temp_c')} מעלות, "
            f"{data.get('condition')}. הנתון הגיע מהכלי (נכון ל-{data.get('fetched_at')})."
        )

    if tools and any(k in text.lower() for k in ("מזג", "טמפר", "weather", "תל אביב", "ירושלים", "אילת")):
        location = "Tel Aviv"
        if "ירושלים" in text or "jerusalem" in text.lower():
            location = "Jerusalem"
        elif "אילת" in text or "eilat" in text.lower():
            location = "Eilat"
        return _fake_reply(
            None,
            [{"id": "call_demo", "name": "get_weather", "arguments": json.dumps({"location": location})}],
        )

    if tools:
        return _fake_reply("בירת צרפת היא פריז.")

    return _fake_reply(
        "אין לי גישה למזג אוויר בזמן אמת, אז אני לא יכולה לתת טמפרטורה עדכנית. "
        "אפשר לנחש שבחודשים החמים זה סביב 30 מעלות – אבל זה ניחוש, לא מדידה חיה."
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
