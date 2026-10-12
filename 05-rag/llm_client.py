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

# מילות מפתח לקבוצות משמעות – כולל תחום שיעורי הבית (ביטוח רכב),
# כדי שההדגמה המקומית תעבוד בלי OpenAI.
_TOPIC_GROUPS = [
    (0, ["גלישה", "אינטרנט", "נפח", "דאטה", "גולש", "מרחיב", "מוסיפ", "אזל", "נגמר", "חבילה"]),
    (1, ["חיוב", "כפול", "חשבון", "תשלום", "החזר", "חויב", "פעמיים"]),
    (2, ["סים", "כרטיס", "pin", "puk", "ננעל", "מכשיר", "טלפון"]),
    (3, ["שעות", "פתוח", "מוקד", "סניף", "פעילות"]),
    (4, ["מסך", "נפילה", "תיקון"]),
    (5, ["נדידה", "חוץ לארץ", "נדוד"]),
    (6, ["מזג", "אוויר", "גשם", "טמפר", "weather"]),
    (7, ["ביטול", "מבטל", "מסלול"]),
    (8, ["תאונה", "התנגש", "פגיעה", "מכונית", "אוטו", "הצעד", "תביעה", "מגיש", "דיווח"]),
    (9, ["שמשה", "זכוכית"]),
    (10, ["גרר", "גרירה", "תקלה"]),
    (11, ["רכב", "נגנב", "גנב", "גנוב"]),
    (12, ["פוליסה", "ביטוח", "כיסוי", "השתתפות", "פיצוי", "נהג", "צעיר", "מחדש"]),
    # תחום שיעורי הבית (מכון כושר)
    (16, ["הקפא", "מקפיא", "עוצר", "עצירה", "נוסע", "השהי"]),
    (17, ["ביטול", "מבטל", "לבטל", "לעזוב", "לסיים"]),
    (18, ["שעות", "פתוח", "סגור", "שבת", "פעילות"]),
    (19, ["שיעור", "קבוצתי", "נרשמ", "הרשמה", "ספינינג", "יוגה", "פילאטיס"]),
    (20, ["חבר", "אורח", "להביא", "מביא"]),
    (21, ["אימון אישי", "מאמן", "אישי", "עולה", "מחיר"]),
    (22, ["ארונית", "ארוניות", "חפצים", "מנעול", "לשמור"]),
    (23, ["נפצע", "פציעה", "כאב", "נפגע"]),
]

REFUSAL = "אני מצטערת, אך המקורות שסופקו אינם מכילים מספיק מידע."


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or default).strip().strip('"').strip("'")


def model_name() -> str:
    return _model or _env("OPENAI_MODEL", "gpt-4o-mini")


def notice() -> str:
    return _notice


def _provider_name() -> str:
    if _client == "mock" or _client is None:
        return "mock"
    base = str(getattr(_client, "base_url", ""))
    if "generativelanguage.googleapis.com" in base:
        return "gemini"
    return "openai"


def embedding_model_name() -> str:
    if _client is None:
        _connect()
    if _client == "mock":
        return "demo-local (וקטורים מקומיים)"
    if _provider_name() == "gemini":
        return _env("GEMINI_EMBEDDING_MODEL") or "gemini-embedding-001"
    return _env("OPENAI_EMBEDDING_MODEL") or "text-embedding-3-small"


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


def _rag_mock(question: str):
    """מדמה מודל שמציית ל-Guardrails: עונה רק ממה שבהקשר, אחרת מסרב."""
    context = question.split("הקשר:", 1)[1].split("\n---\n\nשאלה:", 1)[0]
    answers = [
        line.split("תשובה:", 1)[1].strip()
        for line in context.splitlines()
        if line.strip().startswith("תשובה:")
    ]
    if not answers:
        return _fake_reply(REFUSAL)
    return _fake_reply(f"לפי המקורות: {answers[0]}")


def _mock(messages, tools):
    system = _system_text(messages)
    question = _first_user(messages)
    joined = "\n".join(m.get("content") or "" for m in messages)
    obs = joined.count("Observation:")

    if "הקשר:" in question:
        return _rag_mock(question)

    if not system:
        if any(k in question for k in ("מזג", "weather")):
            return _fake_reply("נראה שיהיה חם. זו השערה, בלי בדיקה.")
        if any(k in question for k in ("הזמנה", "משלוח")):
            return _fake_reply(
                "ההזמנה כנראה בדרך ומגיעה מחר. זו תשובה חופשית, בלי מאגר."
            )
        if any(k in question for k in ("חיוב", "חויבתי", "פעמיים")):
            return _fake_reply(
                "לפי מה שאני יודעת מגיע לך החזר מלא מיד, בלי בדיקה. "
                "זו תשובה חופשית – לא ראיתי את החיוב."
            )
        return _fake_reply(
            "בדרך כלל זה מסתדר בשיחה קצרה עם נציג ובעלות של כ-50 ש״ח. "
            "זו תשובה חופשית – לא ראיתי אף מקור של החברה."
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


def _vector_for(text: str) -> list[float]:
    t = (text or "").lower()
    vec = [0.0] * 24
    fingerprint = 0
    for ch in t:
        fingerprint = (fingerprint * 31 + ord(ch)) % 997
    vec[12 + (fingerprint % 3)] += 0.08
    hits = 0
    for dim, keywords in _TOPIC_GROUPS:
        n = sum(1 for kw in keywords if kw in t)
        if n:
            vec[dim] += 2.0 * n
            hits += n
    if hits == 0:
        vec[15] += 1.0
    return vec


def _mock_embed(texts: list[str]) -> list[list[float]]:
    return [_vector_for(text) for text in texts]


def embed(texts):
    """מחזיר וקטור לכל מחרוזת. אותו מודל לשאילתה ולמאגר. temperature לא רלוונטי."""
    global _client, _model, _notice
    if isinstance(texts, str):
        texts = [texts]
    if not texts:
        return []
    if _client is None:
        _connect()

    def call(current):
        if current == "mock":
            return _mock_embed(texts)
        model = embedding_model_name()
        result = current.embeddings.create(model=model, input=texts)
        return [item.embedding for item in result.data]

    try:
        return call(_client)
    except (APIConnectionError, TimeoutError, OSError):
        if _client != "mock":
            _notice = "אין חיבור למודל. רצות בהדגמה מקומית."
            _client, _model = _make("mock")
            return _mock_embed(texts)
        raise RuntimeError("אין חיבור למודל.")
    except (AuthenticationError, APIStatusError) as exc:
        raise RuntimeError(f"שגיאת מפתח/הרשאה: {exc}") from exc
