# בדיקת הצ'קליסט של פרויקט 2 במצב הדגמה מקומי. מריצים:  python check.py
# מדפיס PASS/FAIL לכל סעיף. (עם מודל אמיתי חלק מהסעיפים עשויים להשתנות.)

import asyncio
import os
import sys
from pathlib import Path

os.environ["LLM_PROVIDER"] = "mock"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent import SUMMARY_KEEP, SUMMARY_TRIGGER, Research  # noqa: E402

HERE = Path(__file__).resolve().parent
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, bool(ok), detail))


def tools_in(log: str) -> list[str]:
    return [line.split("(")[0].replace("הופעל ", "") for line in log.splitlines() if line.startswith("הופעל")]


async def main() -> None:
    r = Research()
    thread = "check-1"

    intro = await r.ask("שלום, שמי דנה.", thread)
    q1 = await r.ask("חפשי מה מצב סוכני ה-AI היום", thread)
    q2 = await r.ask("מה כתבו בהערות הצוות על LangGraph?", thread)
    q3 = await r.ask("חפשי מה ההבדל בין LangChain ל-LangGraph", thread)
    recall = await r.ask("מה שמי?", thread)
    fresh = await r.ask("מה שמי?", "check-2")  # thread אחר: אין זיכרון

    t1, t2, t3 = tools_in(q1["log"]), tools_in(q2["log"]), tools_in(q3["log"])

    check("1. create_agent עם @tool: הסוכן הריץ כלים", bool(t1 and t2 and t3), f"{t1} | {t2} | {t3}")
    check("2. חיפוש רשת (web_search)", "web_search" in t1 and "web_search" in t3)
    from tools import scrape_url  # noqa: E402

    scraped = scrape_url.invoke({"url": "https://example.com/ai-agents-2026"})
    check("3. סריקת דף (scrape_url) עם חיתוך", "scrape_url" in t1 and "[נחתך:" in scraped, scraped[-40:])
    check("4. MCP אמיתי: שרת פעיל וכלי search_notes הופעל", "MCP פעיל" in r.mcp_status and "search_notes" in t2, r.mcp_status)
    check("5. rewrite_query לפני web_search", t1[:2] == ["rewrite_query", "web_search"] and t3[:2] == ["rewrite_query", "web_search"])
    check("6. זיכרון: thread_id זוכר שם, thread אחר לא", "דנה" in recall["answer"] and "דנה" not in fresh["answer"], f"{recall['answer']} / {fresh['answer']}")
    check("7. Summarize: הסיכום פעל והשם עדיין נזכר", any(x["summarized"] for x in (q1, q2, q3, recall)) and "דנה" in recall["answer"], f"trigger={SUMMARY_TRIGGER}, keep={SUMMARY_KEEP}")
    check("8. שלוש שאילתות מחקר, ובפלט מקורות", all(x["structured"].sources for x in (q1, q2, q3)), f"{len(q1['structured'].sources)}, {len(q2['structured'].sources)}, {len(q3['structured'].sources)}")
    check("9. ResearchAnswer מובנה (summary, sources, confidence)", q1["structured"].summary and 0 < q1["structured"].confidence <= 1)
    check("10. לוג tool calls (מה הופעל ולמה)", all("למה:" in x["log"] for x in (q1, q2, q3)))
    check("11. שיחה רב-הודעתית", len(intro["context"]) > 0 and "הודעות שמורות" in recall["context"])
    check("12. README קיים", (HERE / "README.md").exists())

    width = max(len(n) for n, _, _ in results)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {detail}")
    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} עברו")
    sys.exit(1 if failed else 0)


asyncio.run(main())
