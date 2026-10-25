# תשתית חיבור למודל – לא חובה להראות בכיתה.
# OpenAI, ואם נחסם (למשל רימון) עובר ל-Gemini או להדגמה מקומית.
# מחזיר אובייקט מודל של LangChain (ChatOpenAI), או מודל מדומה בלי אינטרנט.

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
# הזיכרון אמיתי: המדומה עונה רק ממה שנמצא ברשימת ההודעות שקיבל.
# מחקר באינטרנט: rewrite_query → web_search → scrape_url. מחקר בהערות הפנימיות: search_notes (MCP).

_NAME_RE = re.compile(r"(?:שמי|קוראים לי)\s+(\w+)")
_URL_RE = re.compile(r"https?://[^\s\]\)]+")
_RECALL = ("מה שמי", "איך קוראים לי", "מה אמרתי")
_NOTES = ("הערות", "פנימי", "הצוות", "notes")
_RESEARCH = ("חפשי", "חפש", "מצבים", "מה ההבדל", "מה מצב", "כמה", "עדכני", "מחקר")


def _kind(msg) -> str:
    return type(msg).__name__


def _txt(content) -> str:
    if isinstance(content, list):
        return "\n".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    return str(content)


def _call(name: str, args: dict, n: int) -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": f"call_{n}", "type": "tool_call"}])


class MockChatModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "mock"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        joined = "\n".join(_txt(m.content) for m in messages)
        if "Context Extraction Assistant" in joined:  # קריאת הסיכום של ה-middleware
            said = _NAME_RE.findall(joined)
            text = "## SUMMARY\nהמשתמשת ניהלה שיחת מחקר."
            if said:
                text += f" היא אמרה: שמי {said[-1]}."
            return self._wrap(AIMessage(content=text))

        last_h = max(i for i, m in enumerate(messages) if _kind(m) == "HumanMessage")
        question = _txt(messages[last_h].content)
        before = "\n".join(_txt(m.content) for m in messages[:last_h])
        turn = messages[last_h + 1 :]
        turn_tools = [m for m in turn if _kind(m) == "ToolMessage"]
        done = [getattr(m, "name", "") for m in turn_tools]
        n = len(turn_tools) + 1

        if turn_tools and not self._more_steps(question, done):
            return self._wrap(AIMessage(content=self._final(turn_tools)))

        if any(w in question for w in _RECALL):
            names = _NAME_RE.findall(before)
            text = f"קוראים לך {names[-1]}." if names else "אני לא יודעת. לא אמרת לי."
            return self._wrap(AIMessage(content=text))
        intro = _NAME_RE.search(question)
        if intro:
            return self._wrap(AIMessage(content=f"נעים להכיר, {intro.group(1)}."))

        if any(w in question for w in _NOTES):
            if "search_notes" not in done:
                return self._wrap(_call("search_notes", {"query": question}, n))
        elif any(w in question for w in _RESEARCH):
            if "rewrite_query" not in done:
                return self._wrap(_call("rewrite_query", {"query": question}, n))
            if "web_search" not in done:
                rewritten = next((_txt(m.content) for m in turn_tools if m.name == "rewrite_query"), question)
                return self._wrap(_call("web_search", {"query": rewritten}, n))
            if "scrape_url" not in done and "סרוק" in question + "סרוק":  # תמיד סורקת את התוצאה הראשונה
                search = next(_txt(m.content) for m in turn_tools if m.name == "web_search")
                urls = _URL_RE.findall(search)
                if urls and "הבדל" not in question:
                    return self._wrap(_call("scrape_url", {"url": urls[0]}, n))
        if turn_tools:
            return self._wrap(AIMessage(content=self._final(turn_tools)))
        return self._wrap(AIMessage(content="אני עוזרת מחקר. אפשר לבקש חיפוש ברשת, או חיפוש בהערות הפנימיות."))

    @staticmethod
    def _more_steps(question: str, done: list) -> bool:
        """האם צעד נוסף צפוי בתור הזה (כדי לא לענות לפני שסיימנו את שרשרת הכלים)."""
        if any(w in question for w in _NOTES):
            return "search_notes" not in done
        if any(w in question for w in _RESEARCH):
            if "web_search" not in done:
                return True
            return "scrape_url" not in done and "הבדל" not in question
        return False

    @staticmethod
    def _final(tool_msgs) -> str:
        sources, parts = [], []
        for m in tool_msgs:
            text = _txt(m.content)
            sources += _URL_RE.findall(text)
            if getattr(m, "name", "") == "search_notes":
                sources += re.findall(r"\[(note-\d+)\]", text)
            if getattr(m, "name", "") in ("scrape_url", "search_notes"):
                parts.append(text.strip()[:220])
        if not parts:
            first = next((_txt(m.content) for m in tool_msgs if getattr(m, "name", "") == "web_search"), "")
            parts.append(first.splitlines()[0] if first else "לא נמצא מידע.")
        uniq = list(dict.fromkeys(sources))
        tail = " מקורות: " + ", ".join(uniq) if uniq else ""
        return "לפי המחקר: " + " ".join(parts) + tail

    @staticmethod
    def _wrap(msg: AIMessage) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=msg)])
