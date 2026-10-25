# קובץ 3 – תיעוד (recorder)
# אוסף את כל מה שקרה: כל קריאה למודל (עם הפרומפט שלה) וכל צעד של הקוד.
# כך אפשר לספור קריאות ולהראות מי עשה מה.

import threading

from llm_client import complete


def messages_text(messages) -> str:
    lines = []
    for msg in messages:
        lines.append(f"[{msg.get('role', '')}]")
        if msg.get("content"):
            lines.append(msg["content"])
        lines.append("")
    return "\n".join(lines).strip()


class Trace:
    def __init__(self) -> None:
        self.steps: list[str] = []
        self.prompts: list[str] = []
        self.calls = 0
        self._lock = threading.Lock()

    def say(self, text: str) -> None:
        with self._lock:
            self.steps.append(text)

    def llm(self, label: str, messages) -> str:
        """קריאה אחת למודל. נספרת ונרשמת."""
        reply = complete(messages)
        content = (reply.choices[0].message.content or "").strip()
        with self._lock:
            self.calls += 1
            self.prompts.append(f"===== קריאה {self.calls} · {label} =====\n{messages_text(messages)}")
        return content

    def numbered_steps(self) -> str:
        return "\n".join(f"{i}. {s}" for i, s in enumerate(self.steps, 1))

    def prompt_text(self) -> str:
        return "\n\n".join(self.prompts)
