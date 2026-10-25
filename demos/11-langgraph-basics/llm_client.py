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
# מודל מדומה שמדבר עם LangChain/LangGraph כמו מודל אמיתי: מחזיר tool_calls או תשובה סופית.
# הוא יודע אם נקשרו אליו כלים (bind_tools), וקורא הכול מרשימת ההודעות שקיבל.

_ACC_RE = re.compile(r"(?:לקוח|מנוי|חבר)\s*(?:מספר\s*)?(\d+)")
_NAME_RE = re.compile(r"(?:שמי|קוראים לי)\s+(\w+)")
_RECALL = ("מה שמי", "איך קוראים לי", "מה אמרתי")
_POLICY_WORDS = ("מדיניות", "החזר", "ביטול", "כמה זמן", "איחור", "השאלה", "הארכה")


def _kind(msg) -> str:
    return type(msg).__name__


def _call(name: str, args: dict, n: int) -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": f"call_{n}", "type": "tool_call"}])


def _facts(text: str) -> dict:
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except ValueError:
        return {}


class MockChatModel(BaseChatModel):
    tools_bound: bool = False

    @property
    def _llm_type(self) -> str:
        return "mock"

    def bind_tools(self, tools, **kwargs):
        return self.model_copy(update={"tools_bound": True})

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        last_h = max(i for i, m in enumerate(messages) if _kind(m) == "HumanMessage")
        question = str(messages[last_h].content)
        before = "\n".join(str(m.content) for m in messages[:last_h])
        turn_tools = [m for m in messages[last_h + 1 :] if _kind(m) == "ToolMessage"]
        n = len(turn_tools) + 1

        intro = _NAME_RE.search(question)
        if intro:
            return self._wrap(AIMessage(content=f"נעים להכיר, {intro.group(1)}."))
        if any(w in question for w in _RECALL):
            names = _NAME_RE.findall(before)
            text = f"קוראים לך {names[-1]}." if names else "אני לא יודעת. לא אמרת לי."
            return self._wrap(AIMessage(content=text))

        acc = _ACC_RE.search(question)
        if not self.tools_bound:  # שלב 1: מודל בלי כלים
            if acc:
                return self._wrap(AIMessage(content="לפי מה שאני יודעת מגיע לך החזר מלא מיד, בלי בדיקה. לא ראיתי את החשבון."))
            return self._wrap(AIMessage(content="אין לי כלים לבדוק את זה. אני עונה רק מהידע הכללי שלי."))

        if turn_tools:
            return self._wrap(AIMessage(content=self._final(turn_tools)))
        if acc:
            return self._wrap(_call("get_account", {"customer_id": acc.group(1)}, n))
        if any(w in question for w in _POLICY_WORDS):
            return self._wrap(_call("search_sources", {"query": question}, n))
        return self._wrap(AIMessage(content="אני עוזרת בחיובים ובמדיניות החברה, לא בנושא הזה."))

    def _final(self, tool_msgs) -> str:
        last = tool_msgs[-1]
        if getattr(last, "status", "") == "error":
            return f"לא הצלחתי לבדוק כרגע: {last.content}"
        parts = []
        for m in tool_msgs:
            facts = _facts(str(m.content))
            parts.append(f"בדקתי: {facts['note']}" if "note" in facts else str(m.content).strip())
        return " ".join(parts)

    @staticmethod
    def _wrap(msg: AIMessage) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=msg)])
