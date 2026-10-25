# תשתית חיבור למודל – לא חובה להראות בכיתה.
# OpenAI, ואם נחסם (למשל רימון) עובר ל-Gemini או להדגמה מקומית.
# מחזיר אובייקט מודל של LangChain (ChatOpenAI), או מודל מדומה בלי אינטרנט.

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_openai import ChatOpenAI

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

_model = None
_notice = ""


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or default).strip().strip('"').strip("'")


def notice() -> str:
    return _notice


def _reachable(url: str) -> bool:
    try:
        import httpx

        httpx.get(url, timeout=5.0)
        return True
    except Exception:
        return False


def _openai() -> ChatOpenAI:
    key = _env("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("חסר OPENAI_API_KEY ב-.env")
    kwargs = {"api_key": key, "model": _env("OPENAI_MODEL", "gpt-4o-mini"), "temperature": 0, "timeout": 30}
    if _env("OPENAI_BASE_URL"):
        kwargs["base_url"] = _env("OPENAI_BASE_URL")
    return ChatOpenAI(**kwargs)


def _gemini() -> ChatOpenAI:
    key = _env("GEMINI_API_KEY") or _env("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("חסר GEMINI_API_KEY ב-.env")
    return ChatOpenAI(
        api_key=key,
        base_url=GEMINI_URL,
        model=_env("GEMINI_MODEL") or "gemini-2.0-flash",
        temperature=0,
        timeout=30,
    )


def _connect():
    global _notice
    wanted = (_env("LLM_PROVIDER", "auto") or "auto").lower()
    if wanted in {"mock", "demo", "offline"}:
        _notice = "מצב הדגמה מקומי – בלי אינטרנט."
        return MockChatModel()
    if wanted == "gemini":
        return _gemini()
    if wanted == "auto":
        if _env("OPENAI_API_KEY") and _reachable("https://api.openai.com/v1/models"):
            return _openai()
        if (_env("GEMINI_API_KEY") or _env("GOOGLE_API_KEY")) and _reachable(
            "https://generativelanguage.googleapis.com"
        ):
            _notice = "OpenAI נחסם. עובדים עם Gemini."
            return _gemini()
        _notice = "אין חיבור למודל. רצות בהדגמה מקומית."
        return MockChatModel()
    return _openai()


def get_model() -> BaseChatModel:
    global _model
    if _model is None:
        _model = _connect()
    return _model


# ---- הדגמה מקומית (mock) ----
# מודל מדומה שמדבר עם LangChain כמו מודל אמיתי: מחזיר tool_calls או תשובה סופית.
# הוא קורא את ההודעות (שאלה, תוצאות כלים) ולא מכיר תחום מסוים.

_ACC_RE = re.compile(r"(?:לקוח|מנוי|חבר)\s*(?:מספר\s*)?(\d+)")
_ORD_RE = re.compile(r"(?:הזמנה|השאלה|בקשה)\s*(?:מספר\s*)?(\d+)")
_MATH_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(כפול|ועוד|פלוס|פחות)\s*(\d+(?:\.\d+)?)")
_OPS = {"כפול": "*", "ועוד": "+", "פלוס": "+", "פחות": "-"}
_POLICY_WORDS = ("מדיניות", "החזר", "ביטול", "כמה זמן", "איחור", "קנס", "השאלה")


def _kind(msg) -> str:
    return type(msg).__name__


def _call(name: str, args: dict, n: int) -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": f"call_{n}", "type": "tool_call"}])


def _facts(text: str) -> list[dict]:
    out = []
    try:
        out.append(json.loads(text))
    except ValueError:
        pass
    return out


def _final(question: str, tool_msgs: list) -> str:
    last = tool_msgs[-1]
    if getattr(last, "status", "") == "error":
        return f"לא הצלחתי לבדוק כרגע: {last.content}. אפשר לנסות שוב בעוד רגע."
    parts = []
    for m in tool_msgs:
        facts = _facts(m.content)
        if facts and "note" in facts[0]:
            parts.append(f"בדקתי: {facts[0]['note']}")
        elif facts and "result" in facts[0]:
            parts.append(f"התוצאה: {facts[0]['result']}")
        else:
            parts.append(m.content.strip())
    return " ".join(parts)


class MockChatModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "mock"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        has_system = any(_kind(m) == "SystemMessage" for m in messages)
        humans = [m for m in messages if _kind(m) == "HumanMessage"]
        question = humans[0].content if humans else ""
        tool_msgs = [m for m in messages if _kind(m) == "ToolMessage"]
        n = len(tool_msgs) + 1

        if not has_system:
            return self._wrap(AIMessage(content=self._guess(question)))

        acc, order = _ACC_RE.search(question), _ORD_RE.search(question)
        math = _MATH_RE.search(question)
        if order:
            msg = _call("lookup_order", {"order_id": order.group(1)}, n) if not tool_msgs else AIMessage(content=_final(question, tool_msgs))
        elif acc:
            if not tool_msgs:
                msg = _call("get_account", {"customer_id": acc.group(1)}, n)
            elif len(tool_msgs) == 1:
                # המדומה מנסח שאילתה קצרה (מודל אמיתי מנסח לבד)
                query = "חיוב כפול" if any(w in question for w in ("פעמיים", "כפול")) else question.replace(acc.group(0), "")
                msg = _call("search_sources", {"query": query}, n)
            else:
                msg = AIMessage(content=_final(question, tool_msgs))
        elif math:
            a, word, b = math.groups()
            msg = _call("calculator", {"expression": f"{a}{_OPS[word]}{b}"}, n) if not tool_msgs else AIMessage(content=_final(question, tool_msgs))
        elif any(w in question for w in _POLICY_WORDS):
            msg = _call("search_sources", {"query": question}, n) if not tool_msgs else AIMessage(content=_final(question, tool_msgs))
        elif any(w in question for w in ("מזג", "חדשות", "היום")):
            msg = _call("web_search", {"query": question}, n) if not tool_msgs else AIMessage(content=_final(question, tool_msgs))
        else:
            msg = AIMessage(content="אני עוזרת רק בחיובים, הזמנות ומדיניות החברה, לא בנושא הזה.")
        return self._wrap(msg)

    @staticmethod
    def _wrap(msg: AIMessage) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=msg)])

    @staticmethod
    def _guess(question: str) -> str:
        if any(w in question for w in ("מזג", "weather")):
            return "נראה שיהיה חם. זו השערה, בלי בדיקה."
        if _ORD_RE.search(question):
            return "ההזמנה כנראה בדרך ומגיעה מחר. זו תשובה חופשית, בלי מאגר."
        if _MATH_RE.search(question):
            return "בערך 80. זו הערכה בלי מחשבון."
        return "לפי מה שאני יודעת מגיע לך החזר מלא מיד, בלי בדיקה. לא ראיתי את החשבון."
