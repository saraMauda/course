# trace.py – תיעוד מקומי של מה שרץ (כמו span פשוט).
# LangSmith עושה את זה אוטומטית כשמגדירים משתני סביבה. כאן יש תמיד גרסה מקומית:
# רשימה לתצוגה בחלון, וקובץ JSONL (traces.jsonl) שאפשר לצרף לבדיקה.

import json
import time
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent / "traces.jsonl"
_events: list[dict] = []


def start() -> None:
    _events.clear()


def log(kind: str, detail: str) -> None:
    _events.append({"t": round(time.time(), 3), "kind": kind, "detail": detail})


def lines() -> list[str]:
    return [f"{e['kind']}: {e['detail']}" for e in _events]


def flush(question: str, notebook: str, thread: str) -> None:
    record = {"question": question, "notebook": notebook, "thread": thread, "events": list(_events)}
    try:
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass  # לוג מקומי הוא נוחות, לא דרישה
