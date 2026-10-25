# קובץ 1 – Discovery
# האפליקציה (לא המודל) סורקת את תיקיית skills, קוראת כל SKILL.md
# ושומרת name / description / body. זה ה-SkillsStore.

from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent / "skills"


def _parse(text: str) -> tuple[dict, str]:
    """frontmatter (בין שתי שורות ---) + גוף הקובץ."""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta, parts[2].strip()


def load_skills() -> dict:
    store = {}
    for path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        meta, body = _parse(path.read_text(encoding="utf-8"))
        if not meta.get("name") or not meta.get("description"):
            continue
        store[meta["name"]] = {
            "name": meta["name"],
            "description": meta["description"],
            "body": body,
            "location": str(path.parent),
        }
    return store


def catalog(store: dict) -> str:
    """השכבה הראשונה של Progressive Disclosure: name + description בלבד."""
    return "\n".join(f"- {s['name']}: {s['description']}" for s in store.values())
