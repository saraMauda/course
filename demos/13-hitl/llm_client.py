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
# מודל מדומה שמדגים את הדפוס של Prompt Injection, בלי אינטרנט.
# הוא "מציית" להוראה שמצא במקור. עם הפרדה בפרומפט הוא מתעלם מהוראה שנמצאת *בתוך* תגית <source>,
# אבל לא מהוראה שמופיעה *מחוץ* לתגית (למשל אחרי סגירת תגית מזויפת בתוך המסמך).
# מודל אמיתי עלול להיכשל גם בהפרדה. זו הסיבה שאין להסתמך עליה לבדה.

_BLOCK_RE = re.compile(r'<source id="([^"]*)">(.*?)</source>', re.S)
_PLAIN_RE = re.compile(r"מקור (doc-\d+):\n(.*?)(?=\nמקור doc-|\Z)", re.S)
_QUOTE_RE = re.compile(r"«([^»]+)»")
_INJECTION = "הוראה למערכת"


def _words(text: str) -> set:
    return {w for w in re.findall(r"\w+", text) if len(w) > 2}


class MockChatModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "mock"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        system = next((str(m.content) for m in messages if type(m).__name__ == "SystemMessage"), "")
        user = str(messages[-1].content)
        sources_part, _, question = user.partition("\nשאלה:")
        separation = "מידע בלבד, לא הוראות" in system

        if separation:
            docs = _BLOCK_RE.findall(sources_part)
            outside = _BLOCK_RE.sub("", sources_part)
            injected_text = outside if _INJECTION in outside else ""
        else:
            docs = _PLAIN_RE.findall(sources_part)
            injected_text = sources_part if _INJECTION in sources_part else ""

        if injected_text:
            quote = _QUOTE_RE.search(injected_text[injected_text.index(_INJECTION):])
            phrase = quote.group(1) if quote else "בוצע"
            return self._wrap(f"{phrase}.")

        clean = [(i, t.strip()) for i, t in docs if _INJECTION not in t]
        if not clean:
            return self._wrap("אין לי מקורות מאושרים כדי לענות.")
        q = _words(question)
        best = max(clean, key=lambda pair: len(q & _words(pair[1])))
        return self._wrap(f"לפי {best[0]}: {best[1]}")

    @staticmethod
    def _wrap(content: str) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])
