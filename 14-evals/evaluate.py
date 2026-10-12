# קובץ 5 – ה-Eval
# מריץ את כל ה-Golden set על גרסה אחת של הצנרת ומחזיר ציונים.
# שני מדדים נפרדים: האם **נשלף** המקור הנכון, והאם **התשובה** נכונה.

from golden import GOLDEN
from pipeline import run_pipeline

# כל גרסה = שינוי אחד. כך רואים מה שינוי גרם.
CONFIGS = {
    "A — סף 0.45 + Guardrails (הנוכחית)": {"threshold": 0.45, "guardrails": True},
    "B — בלי Guardrails": {"threshold": 0.45, "guardrails": False},
    "C — בלי סף (תמיד top-K)": {"threshold": -1.0, "guardrails": True},
    "D — סף גבוה 0.92": {"threshold": 0.92, "guardrails": True},
}

HISTORY: list[dict] = []


def run_eval(config_name: str) -> dict:
    config = CONFIGS[config_name]
    rows = []
    for item in GOLDEN:
        out = run_pipeline(item["question"], config)
        hit_ids = [h["id"] for h in out["hits"]]
        in_scope = item["source"] is not None
        retrieval_ok = (item["source"] in hit_ids) if in_scope else (len(hit_ids) == 0)
        answer_ok = item["must_contain"] in out["answer"]
        best = out["ranked"][0]
        rows.append(
            {
                "question": item["question"],
                "kind": item["kind"],
                "in_scope": in_scope,
                "top1": f"{best['id']} ({best['score']:.2f})",
                "retrieval_ok": retrieval_ok,
                "answer_ok": answer_ok,
                "answer": out["answer"],
            }
        )

    inside = [r for r in rows if r["in_scope"]]
    outside = [r for r in rows if not r["in_scope"]]
    summary = {
        "config": config_name,
        "retrieval": sum(r["retrieval_ok"] for r in inside),
        "n_inside": len(inside),
        "refusal": sum(r["answer_ok"] for r in outside),
        "n_outside": len(outside),
        "answers": sum(r["answer_ok"] for r in inside),
        "passed": sum(r["answer_ok"] for r in rows),
        "total": len(rows),
    }
    HISTORY.append(summary)
    return {"rows": rows, "summary": summary}
