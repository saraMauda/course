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


def _user_text(messages) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content") or ""
    return ""


def _system_text(messages) -> str:
    for msg in messages:
        if msg.get("role") == "system":
            return msg.get("content") or ""
    return ""


def _mock(messages, tools):
    text = _user_text(messages)
    system = _system_text(messages)
    low = text.lower()

    if not system:
        if any(k in low for k in ("פישינג", "סיסמ", "פורצ", "האק")):
            return _fake_reply(
                "כן, זה נשמע בעייתי – כנראה ניסיון להונאה או פריצה. "
                "אבל זו תשובה חופשית, בלי מבנה קבוע לקוד."
            )
        if any(k in text for k in ("פיצה", "הזמין", "הזמנה")):
            return _fake_reply(
                "נשמע שהלקוח רוצה להזמין. אפשר לשאול איזה תוספות. "
                "זו תשובה חופשית, בלי JSON."
            )
        return _fake_reply(
            "הטקסט נשמע בסדר, לא נראה לי בעייתי. "
            "זו תשובה חופשית – אין שדות קבועים שהקוד יכול לבדוק."
        )

    if any(k in system for k in ("intent", "in_scope", "מסעדה")):
        if any(k in text for k in ("פיצה", "הזמין", "הזמנה", "להזמין")):
            data = {
                "intent": "order",
                "in_scope": True,
                "answer": "כן, אפשר להזמין. איזה תוספות?",
            }
        elif any(k in text for k in ("שע", "פתוח", "סגור")):
            data = {
                "intent": "hours",
                "in_scope": True,
                "answer": "אנחנו פתוחים עד 23:00.",
            }
        else:
            data = {
                "intent": "other",
                "in_scope": False,
                "answer": "אני עוזרת רק בהזמנות ובשעות פתיחה.",
            }
        return _fake_reply(json.dumps(data, ensure_ascii=False))

    if any(k in low for k in ("פישינג", "סיסמ", "פורצ", "האק", "התעלמי")):
        data = {
            "violation": "yes",
            "category": "פריצה" if "פורצ" in text or "האק" in low else "פישינג",
            "riskLevel": "red",
            "manipulative": "התעלמי" in text or "סיפור" in text,
            "reason": "מעטפת שמנסה לעקוף מדיניות."
            if ("התעלמי" in text or "סיפור" in text)
            else "בקשה ישירה לתוכן אסור.",
        }
    elif any(k in text for k in ("מזג", "weather")):
        data = {
            "violation": "no",
            "category": "שאלה כללית",
            "riskLevel": "green",
            "manipulative": False,
            "reason": "שאלה תמימה בלי תוכן אסור.",
        }
    else:
        data = {
            "violation": "no",
            "category": "קוד",
            "riskLevel": "green",
            "manipulative": False,
            "reason": "בקשת קוד תמימה, בלי ניסיון לעקוף מדיניות.",
        }
    return _fake_reply(json.dumps(data, ensure_ascii=False))


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
