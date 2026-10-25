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


def _catalog_names(tools) -> list[str]:
    """שמות ה-skills מתוך הקטלוג שבתיאור הכלי activate_skill."""
    names = []
    for tool in tools or []:
        desc = tool.get("function", {}).get("description", "")
        for line in desc.splitlines():
            if line.startswith("- "):
                names.append(line[2:].split(":", 1)[0].strip())
    return names


def _skill_reply(name: str):
    """מדמה מודל שקרא את ה-SKILL.md ועובד לפיו."""
    if name == "complaint-reply":
        return _fake_reply(
            "שלום,\n"
            "ראינו שחויבת פעמיים על אותה חבילה, וזה לא אמור לקרות.\n"
            "בדקנו בחשבון: יש שני חיובים זהים באותו חודש.\n"
            "לפי המדיניות, חיוב אחד יוחזר תוך 5 ימי עסקים.\n"
            "אין צורך בפעולה מצידך – נשלח אישור במייל ביום ההחזר."
        )
    if name == "policy-summary":
        return _fake_reply(
            "סיכום:\n"
            "• ביטול נכנס בסוף מחזור החיוב.\n"
            "• החזר רק על חיוב כפול, תוך 5 ימי עסקים.\n"
            "• אין החזר על שימוש שכבר נצרך.\n"
            "סיכונים:\n"
            "• לקוחה שמבטלת באמצע חודש תחויב עד סוף המחזור."
        )
    if name == "appointment-reminder":
        return _fake_reply(
            "שלום דנה,\n"
            "תזכורת: יש לך תור לניקוי שיניים ביום שלישי ב-10:30, ברחוב הרצל 12.\n"
            "נא להגיע 10 דקות מוקדם ולהביא תעודה מזהה.\n"
            "לביטול או שינוי – עד 24 שעות לפני, בטלפון 03-1234567."
        )
    return _fake_reply(
        "הערת העברה:\n"
        "לקוחה: —\n"
        "בעיה: —\n"
        "מה כבר נעשה: —\n"
        "מה מבקשים מהנציג הבכיר: —"
    )


def _mock(messages, tools):
    last = messages[-1]
    role = last.get("role")
    text = last.get("content") or ""
    request = next((m.get("content") or "" for m in messages if m.get("role") == "user"), "")

    if role == "tool":
        if text.startswith("לא נמצא"):
            return _fake_reply("לא מצאתי skill מתאים, אז אענה מהידע הכללי שלי.")
        name = text.split("הופעל skill:", 1)[-1].split("\n", 1)[0].strip()
        return _skill_reply(name)

    is_complaint = any(k in request for k in ("חויבתי", "כועס", "תלונה", "ללקוחה"))
    is_policy = any(k in request for k in ("סכמי", "סיכום", "מדיניות"))
    is_reminder = any(k in request for k in ("תזכורת", "תור"))
    is_escalation = any(k in request for k in ("בכיר", "להעביר", "הסלמה"))

    if tools:
        names = _catalog_names(tools)
        wanted = None
        if is_reminder:
            wanted = "appointment-reminder"
        elif is_escalation:
            wanted = "escalation-note"
        elif is_policy:
            wanted = "policy-summary"
        elif is_complaint:
            wanted = "complaint-reply"
        if wanted and wanted in names:
            return _fake_reply(
                None,
                [{"id": "call_skill", "name": "activate_skill", "arguments": json.dumps({"name": wanted})}],
            )
        return _fake_reply("בירת צרפת היא פריז.")

    if is_reminder:
        return _fake_reply(
            "היי! רק להזכיר שיש לך תור בקרוב. נשמח לראות אותך, ואל תשכחי שהטיפול כלול בביטוח! "
            "תודה והמשך יום נעים!"
        )
    if is_policy:
        return _fake_reply(
            "המדיניות עוסקת בביטולים והחזרים. בקצרה, אפשר לבטל והחזרים ניתנים בתנאים מסוימים. "
            "כדאי לקרוא את המסמך המלא."
        )
    if is_complaint:
        return _fake_reply(
            "שלום, אנחנו מצטערים מאוד על אי הנוחות! נחזיר לך את כל הכסף מיד ונוסיף פיצוי. "
            "תודה על הסבלנות והמשך יום נעים!"
        )
    return _fake_reply("בירת צרפת היא פריז.")


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
