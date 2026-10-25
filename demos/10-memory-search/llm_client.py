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
# הזיכרון כאן אמיתי: המדומה עונה רק ממה שנמצא ברשימת ההודעות שקיבל.
# אם ההודעה על השם לא ברשימה (אין זיכרון, או שנחתכה) – הוא לא יודע.

_NAME_RE = re.compile(r"(?:שמי|קוראים לי)\s+(\w+)")
_URL_RE = re.compile(r"https?://[^\s]+")
_RECALL = ("מה שמי", "איך קוראים לי", "מה אמרתי")
_SCRAPE = ("תסרק", "סרוק", "סרקי", "תקרא את הדף")
_SEARCH = ("חפש", "חיפוש", "כמה", "עדכני")


def _kind(msg) -> str:
    return type(msg).__name__


def _call(name: str, args: dict, n: int) -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": f"call_{n}", "type": "tool_call"}])


class MockChatModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "mock"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        joined = "\n".join(str(m.content) for m in messages)
        if "Context Extraction Assistant" in joined:  # קריאת הסיכום של ה-middleware
            said = _NAME_RE.findall(joined)
            text = "## SUMMARY\nהמשתמשת ניהלה שיחת מחקר על כלי סוכנים."
            if said:
                text += f" היא אמרה: שמי {said[-1]}."
            return self._wrap(AIMessage(content=text))

        last_h = max(i for i, m in enumerate(messages) if _kind(m) == "HumanMessage")
        question = str(messages[last_h].content)
        before = "\n".join(str(m.content) for m in messages[:last_h])
        turn_tools = [m for m in messages[last_h + 1 :] if _kind(m) == "ToolMessage"]
        n = len(turn_tools) + 1

        if turn_tools:
            return self._wrap(AIMessage(content=self._final(turn_tools[-1])))

        if any(w in question for w in _RECALL):
            names = _NAME_RE.findall(before)
            text = f"קוראים לך {names[-1]}." if names else "אני לא יודעת. לא אמרת לי."
            return self._wrap(AIMessage(content=text))
        intro = _NAME_RE.search(question)
        if intro:
            return self._wrap(AIMessage(content=f"נעים להכיר, {intro.group(1)}."))
        if any(w in question for w in _SCRAPE):
            searches = [m for m in messages if _kind(m) == "ToolMessage" and getattr(m, "name", "") == "web_search"]
            urls = _URL_RE.findall(searches[-1].content) if searches else []
            if not urls:
                return self._wrap(AIMessage(content="אין לי כתובת לסרוק. אפשר קודם לבקש חיפוש?"))
            return self._wrap(_call("scrape_url", {"url": urls[0]}, n))
        if any(w in question for w in _SEARCH):
            return self._wrap(_call("web_search", {"query": question}, n))
        return self._wrap(AIMessage(content="אני עוזרת במחקר. אפשר לבקש ממני חיפוש, או לסרוק דף."))

    @staticmethod
    def _final(tool_msg) -> str:
        name = getattr(tool_msg, "name", "")
        text = str(tool_msg.content)
        if name == "web_search":
            urls = _URL_RE.findall(text)
            first = text.splitlines()[0] if text else ""
            return f"מצאתי {len(urls)} מקורות. הראשון: {first}"
        if name == "scrape_url":
            return f"מהדף: {text[:160]}…"
        return text

    @staticmethod
    def _wrap(msg: AIMessage) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=msg)])
