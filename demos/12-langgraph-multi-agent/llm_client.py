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
# מודל מדומה: כל תפקיד (KB, ACCOUNT, WEB, SYNTH) מזוהה לפי התגית בשורה הראשונה של ה-System prompt.
# הוא רק מסכם את הנתונים שקיבל, ולא מכיר תחום מסוים.

_JSON_RE = re.compile(r"\{.*\}")


def _tag(messages) -> str:
    for m in messages:
        if type(m).__name__ == "SystemMessage":
            return str(m.content).strip().splitlines()[0]
    return ""


def _data_part(text: str) -> str:
    return text.split("נתונים:", 1)[1].strip() if "נתונים:" in text else ""


class MockChatModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "mock"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        tag = _tag(messages)
        text = str(messages[-1].content)
        if tag == "[SYNTH]":
            return self._wrap(self._synth(text))
        data = _data_part(text)
        if not data or data == "אין נתונים":
            return self._wrap("אין מידע.")
        match = _JSON_RE.search(data)
        if match:
            try:
                note = json.loads(match.group(0)).get("note")
                if note:
                    return self._wrap(note)
            except ValueError:
                pass
        return self._wrap(" ".join(data.split()))

    def _synth(self, text: str) -> str:
        lines = [l for l in text.splitlines() if ": " in l and l.split(":", 1)[0] in ("kb", "account", "web")]
        notes = [l.split(": ", 1)[1] for l in lines]
        errors = [n for n in notes if n.startswith("שגיאה")]
        useful = [n for n in notes if n and n != "אין מידע." and not n.startswith("שגיאה")]
        if not useful:
            answer = "לא מצאתי מספיק מידע כדי לענות."
        else:
            answer = "לפי המקורות: " + " ".join(useful)
        if errors:
            answer += " (מקור אחד לא ענה, והתשובה חלקית.)"
        return answer

    @staticmethod
    def _wrap(content: str) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])
