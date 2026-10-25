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
# הטמעה מדומה: שק מילים עם גיבוב ל-512 ממדים (בלי אותיות יחס בתחילת מילה). לא סמנטי, רק מילולי.
# מודל שיחה מדומה: עונה מהמקטעים שקיבל, עם ציטוט [S#]. אם אין מקטעים: סירוב, או web_search אם הופעל.

_DIMS = 512
_PREFIX = "הוכבלמש"


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


def _kind(msg) -> str:
    return type(msg).__name__


class MockChatModel(BaseChatModel):
    tools_bound: bool = False

    @property
    def _llm_type(self) -> str:
        return "mock"

    def bind_tools(self, tools, **kwargs):
        return self.model_copy(update={"tools_bound": True})

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        last_h = max(i for i, m in enumerate(messages) if _kind(m) == "HumanMessage")
        user = str(messages[last_h].content)
        turn_tools = [m for m in messages[last_h + 1 :] if _kind(m) == "ToolMessage"]
        question = user.partition("\nשאלה:")[2].strip()
        chunks = _SOURCE_RE.findall(user.partition("\nשאלה:")[0])

        if turn_tools:
            return self._wrap(AIMessage(content=f"מהרשת (לא מהמקורות שלך): {str(turn_tools[-1].content)[:140]}"))
        if not chunks:
            if self.tools_bound:
                call = {"name": "web_search", "args": {"query": question}, "id": "call_1", "type": "tool_call"}
                return self._wrap(AIMessage(content="", tool_calls=[call]))
            return self._wrap(AIMessage(content="אין מספיק מידע במקורות שאושרו כדי לענות."))
        top = chunks[:2]
        body = " ".join(f"{text.strip()} [{sid}]" for sid, text in top)
        return self._wrap(AIMessage(content=f"לפי המקורות: {body}"))

    @staticmethod
    def _wrap(msg: AIMessage) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=msg)])
