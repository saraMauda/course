# תשתית חיבור למודל – לא חובה להראות בכיתה.
# OpenAI, ואם נחסם (למשל רימון) עובר ל-Gemini או להדגמה מקומית.
# נותן שני דברים: מודל שיחה של LangChain (get_model) ווקטורים להטמעה (embed).

import hashlib
import math
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# טוענים .env לפני כל דבר אחר: כך גם משתני LangSmith (LANGSMITH_*) נכנסים ל-os.environ,
# ו-LangChain/LangGraph מפעילים tracing לבד, בלי שורת קוד נוספת.
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

_provider = ""  # openai | gemini | mock
_model = None
_embedder = None
_notice = ""


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or default).strip().strip('"').strip("'")


def notice() -> str:
    return _notice


def tracing_status() -> str:
    """האם LangSmith פעיל? (רק לפי משתני סביבה. לא נדרש.)"""
    on = _env("LANGSMITH_TRACING").lower() == "true" or _env("LANGCHAIN_TRACING_V2").lower() == "true"
    has_key = bool(_env("LANGSMITH_API_KEY") or _env("LANGCHAIN_API_KEY"))
    if on and has_key:
        return f"LangSmith פעיל (project: {_env('LANGSMITH_PROJECT') or _env('LANGCHAIN_PROJECT') or 'default'})"
    return "LangSmith כבוי. נשאר trace מקומי"


def _reachable(url: str) -> bool:
    try:
        import httpx

        httpx.get(url, timeout=5.0)
        return True
    except Exception:
        return False


def _decide_provider() -> str:
    global _notice
    wanted = (_env("LLM_PROVIDER", "auto") or "auto").lower()
    if wanted in {"mock", "demo", "offline"}:
        _notice = "מצב הדגמה מקומי – בלי אינטרנט."
        return "mock"
    if wanted == "gemini":
        return "gemini"
    if wanted == "auto":
        if _env("OPENAI_API_KEY") and _reachable("https://api.openai.com/v1/models"):
            return "openai"
        if (_env("GEMINI_API_KEY") or _env("GOOGLE_API_KEY")) and _reachable("https://generativelanguage.googleapis.com"):
            _notice = "OpenAI נחסם. עובדים עם Gemini."
            return "gemini"
        _notice = "אין חיבור למודל. רצות בהדגמה מקומית."
        return "mock"
    return "openai"


def _provider_name() -> str:
    global _provider
    if not _provider:
        _provider = _decide_provider()
    return _provider


def provider_name() -> str:
    return _provider_name()


def get_model() -> BaseChatModel:
    global _model
    if _model is not None:
        return _model
    provider = _provider_name()
    if provider == "mock":
        _model = MockChatModel()
    elif provider == "gemini":
        key = _env("GEMINI_API_KEY") or _env("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("חסר GEMINI_API_KEY ב-.env")
        _model = ChatOpenAI(api_key=key, base_url=GEMINI_URL, model=_env("GEMINI_MODEL") or "gemini-2.0-flash", temperature=0, timeout=30)
    else:
        key = _env("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("חסר OPENAI_API_KEY ב-.env")
        kwargs = {"api_key": key, "model": _env("OPENAI_MODEL", "gpt-4o-mini"), "temperature": 0, "timeout": 30}
        if _env("OPENAI_BASE_URL"):
            kwargs["base_url"] = _env("OPENAI_BASE_URL")
        _model = ChatOpenAI(**kwargs)
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    """אותו מודל להטמעה גם למקורות וגם לשאילתה."""
    global _embedder
    provider = _provider_name()
    if provider == "mock":
        return [_mock_vector(t) for t in texts]
    if _embedder is None:
        if provider == "gemini":
            key = _env("GEMINI_API_KEY") or _env("GOOGLE_API_KEY")
            _embedder = OpenAIEmbeddings(api_key=key, base_url=GEMINI_URL, model=_env("GEMINI_EMBEDDING_MODEL") or "gemini-embedding-001", check_embedding_ctx_length=False)
        else:
            kwargs = {"api_key": _env("OPENAI_API_KEY"), "model": _env("OPENAI_EMBEDDING_MODEL") or "text-embedding-3-small"}
            if _env("OPENAI_BASE_URL"):
                kwargs["base_url"] = _env("OPENAI_BASE_URL")
            _embedder = OpenAIEmbeddings(**kwargs)
    return _embedder.embed_documents(list(texts))


# ---- הדגמה מקומית (mock) ----
# הטמעה מדומה: שק מילים עם גיבוב ל-512 ממדים (בלי אותיות יחס בתחילת מילה). מילולית, לא סמנטית.
# מודל שיחה מדומה: עונה מהמקטעים שקיבל, עם ציטוט [S#], ומסרב כשהמקטעים לא מכסים את השאלה.
# הוא מתנהג כמו סוכן ReAct: אם לא מצא מספיק, קורא ל-search_sources, ואז (אם web פעיל) ל-web_search.

_DIMS = 512
_PREFIX = "הוכבלמש"
_STOP = {"איך", "כמה", "למה", "האם", "איפה", "מתי", "מקורות"}


def _tokens(text: str) -> list[str]:
    out = []
    for w in re.findall(r"\w+", text or ""):
        if len(w) > 2:
            for _ in range(2):  # עד שתי אותיות יחס: להחזר → החזר → חזר
                if len(w) > 3 and w[0] in _PREFIX:
                    w = w[1:]
            out.append(w)
    return out


def _mock_vector(text: str) -> list[float]:
    vec = [0.0] * _DIMS
    for tok in _tokens(text):
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        vec[h % _DIMS] += 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


_SOURCE_RE = re.compile(r'<source id="([^"]*)"[^>]*>(.*?)</source>', re.S)
_LINE_RE = re.compile(r"\[(S\d+)#\d+\]\s*(.*)")
_INJECTION = "הוראה למערכת"
_COVERAGE = 0.4  # כמה מהמילים בשאלה חייבות להופיע במקטע כדי שהמדומה "יעז" לענות
_REFUSAL = "אין מספיק מידע במקורות שאושרו כדי לענות."


def _kind(msg) -> str:
    return type(msg).__name__


def _coverage(question: str, text: str) -> float:
    q = {t for t in _tokens(question) if t not in _STOP}
    if not q:
        return 0.0
    return len(q & set(_tokens(text))) / len(q)


def _best(pairs: list[tuple[str, str]], question: str) -> list[tuple[str, str]]:
    """רק מקטעים נקיים (בלי הוראות) שמכסים את השאלה."""
    good = [(sid, text) for sid, text in pairs if _INJECTION not in text and _coverage(question, text) >= _COVERAGE]
    return good[:2]


def _call(name: str, args: dict, n: int) -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": f"call_{n}", "type": "tool_call"}])


class MockChatModel(BaseChatModel):
    tool_names: list = []

    @property
    def _llm_type(self) -> str:
        return "mock"

    def bind_tools(self, tools, **kwargs):
        names = [getattr(t, "name", None) or t.get("name", "") for t in tools]
        return self.model_copy(update={"tool_names": names})

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        system = next((str(m.content) for m in messages if _kind(m) == "SystemMessage"), "")
        last_h = max(i for i, m in enumerate(messages) if _kind(m) == "HumanMessage")
        user = str(messages[last_h].content)
        prev = [str(m.content) for m in messages[:last_h] if _kind(m) == "HumanMessage"]
        turn_tools = [m for m in messages[last_h + 1 :] if _kind(m) == "ToolMessage"]
        context, _, question = user.partition("\nשאלה:")
        question = question.strip() or user

        if any(w in question for w in ("מה שאלתי", "מה אמרתי")):
            return self._text(f"שאלת קודם: {prev[-1]}" if prev else "עוד לא שאלת כלום.")
        if "התעלמי" in question and "התעלמי" in system:
            return self._text("אני לא יכולה להתעלם מהנהלים. אפשר לשאול אותי על המקורות שאושרו.")

        n = len(turn_tools) + 1
        if turn_tools:
            last = turn_tools[-1]
            name, text = getattr(last, "name", ""), str(last.content)
            if name == "search_sources":
                pairs = [(m.group(1), m.group(2)) for m in map(_LINE_RE.match, text.splitlines()) if m]
                good = _best(pairs, question)
                if good:
                    return self._text("לפי המקורות: " + " ".join(f"{t.strip()} [{s}]" for s, t in good))
                if "web_search" in self.tool_names and not any(getattr(t, "name", "") == "web_search" for t in turn_tools):
                    return self._msg(_call("web_search", {"query": question}, n))
                return self._text(_REFUSAL)
            if name == "web_search":
                return self._text(f"מהרשת (לא מהמקורות שלך): {text[:140]}")
            if name == "scrape_url":
                return self._text(f"מהדף: {text[:140]}")
            return self._text(text[:140])

        pairs = _SOURCE_RE.findall(context)
        good = _best(pairs, question)
        if good:
            return self._text("לפי המקורות: " + " ".join(f"{t.strip()} [{s}]" for s, t in good))
        if "search_sources" in self.tool_names:
            return self._msg(_call("search_sources", {"query": question}, n))
        return self._text(_REFUSAL)

    @staticmethod
    def _msg(msg: AIMessage) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=msg)])

    def _text(self, content: str) -> ChatResult:
        return self._msg(AIMessage(content=content))
