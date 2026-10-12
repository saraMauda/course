# תשתית חיבור למודל – לא חובה להראות בכיתה.
# OpenAI, ואם נחסם (למשל רימון) עובר ל-Gemini או להדגמה מקומית.

import json
import re
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


def _tool_names(tools) -> list[str]:
    return [t.get("function", {}).get("name", "") for t in tools or []]


def _call(name: str, args: dict):
    return _fake_reply(
        None,
        [{"id": f"call_{name}", "name": name, "arguments": json.dumps(args, ensure_ascii=False)}],
    )


def _library_mock(request: str, results: list, names: list):
    """תחום שיעורי הבית (ספרייה), כדי שההדגמה המקומית תעבוד בלי OpenAI."""
    if len(results) == 0:
        found = re.search(r"[«\"'](.+?)[»\"']", request)
        return _call("lookup_book", {"title": found.group(1) if found else request})
    if len(results) == 1 and "lookup_loan_policy" in names:
        return _call("lookup_loan_policy", {"topic": "השאלה"})
    try:
        book = json.loads(results[0])
        policy = json.loads(results[1])["policy"]
    except (IndexError, KeyError, json.JSONDecodeError):
        return _fake_reply("לא מצאתי את הספר במאגר הספרייה.")
    if book.get("error"):
        return _fake_reply("לא מצאתי את הספר במאגר הספרייה.")
    if book.get("available"):
        head = f"הספר «{book['title']}» זמין: {book['available']} מתוך {book['copies']} עותקים, {book['location']}."
    else:
        head = f"הספר «{book['title']}» לא זמין כרגע. צפוי לחזור ב-{book['back_on']}."
    return _fake_reply(f"{head} לפי המדיניות: {policy}")


def _mock(messages, tools):
    request = next((m.get("content") or "" for m in messages if m.get("role") == "user"), "")
    results = [m.get("content") or "" for m in messages if m.get("role") == "tool"]
    asks_weather = any(k in request for k in ("מזג", "weather"))

    if not tools:
        if asks_weather:
            return _fake_reply("נראה שיהיה חם. זו השערה, בלי בדיקה.")
        if any(k in request for k in ("ספר", "השאל", "ספרי")):
            return _fake_reply("כן, כל הספרים זמינים תמיד להשאלה, ואפשר להאריך בלי הגבלה. זו תשובה חופשית.")
        return _fake_reply(
            "לפי מה שאני יודעת מגיע לך החזר מלא מיד, בלי בדיקה. "
            "זו תשובה חופשית – אין לי גישה לחשבון שלך."
        )

    if asks_weather:
        return _fake_reply("אין לי כלי שמתאים לשאלה הזאת, ואני לא ממציאה תשובה.")

    names = _tool_names(tools)
    if "lookup_book" in names:
        return _library_mock(request, results, names)
    if len(results) == 0 and "lookup_bill" in names:
        customer = "100" if "100" in request else "312"
        return _call("lookup_bill", {"customer_id": customer})
    if len(results) == 1 and "lookup_policy" in names:
        return _call("lookup_policy", {"topic": "חיוב כפול"})

    try:
        bill = json.loads(results[0])
    except (IndexError, json.JSONDecodeError):
        bill = {}
    charges = bill.get("charges") or []
    if len(charges) >= 2:
        return _fake_reply(
            f"בדקתי את חשבון {bill.get('customer')}: {len(charges)} חיובים זהים של "
            f"{charges[0]} ב{bill.get('month')} על {bill.get('plan')}. "
            "לפי המדיניות מגיע החזר של חיוב אחד תוך 5 ימי עסקים, אחרי אימות."
        )
    return _fake_reply(
        f"בדקתי את חשבון {bill.get('customer', '')}: יש חיוב אחד בלבד. אין חיוב כפול ואין החזר."
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
