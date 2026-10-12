# קובץ 3 – ה-Host
# בלי MCP: בקשה אחת, תשובה אחת.
# עם MCP: מתחברים לשרת → מגלים Tools → מצרפים אותם לקריאה → לולאה:
# המודל מבקש Tool → ה-Client מפעיל אותו בשרת → התוצאה חוזרת למודל.

import asyncio
import json
from pathlib import Path

from client import MCPClient
from llm_client import complete, notice

SERVER_PATH = str(Path(__file__).resolve().parent / "server.py")
MAX_ROUNDS = 4

SYSTEM_PROMPT = """
את עוזרת תמיכה של חברת סלולר. עני בעברית, קצרה וברורה.

אם צריך נתון על חשבון או על מדיניות – השתמשי בכלים שעומדים לרשותך.
אל תמציאי חיוב, סכום או מדיניות.
""".strip()

EXAMPLES = [
    "לקוחה 312 טוענת שחויבה פעמיים. מה מגיע לה?",
    "לקוחה 100 טוענת שחויבה פעמיים. מה מגיע לה?",
    "מה מזג האוויר?",
]
EXAMPLE_TEXT = EXAMPLES[0]


def _as_dict(msg) -> dict:
    data = {"role": "assistant", "content": msg.content}
    if msg.tool_calls:
        data["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.function.name, "arguments": call.function.arguments},
            }
            for call in msg.tool_calls
        ]
    return data


def _to_llm_tool(tool) -> dict:
    """תרגום Tool של MCP לפורמט שהמודל מכיר (Function Calling)."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        },
    }


def _prompt_text(messages, tools) -> str:
    lines = []
    for msg in messages:
        lines.append(f"[{msg.get('role', '')}]")
        if msg.get("content"):
            lines.append(msg["content"])
        if msg.get("tool_calls"):
            lines.append(json.dumps(msg["tool_calls"], ensure_ascii=False, indent=2))
        lines.append("")
    lines.append("--- ה-Tools שה-Host צירף (הגיעו מהשרת, לא נכתבו כאן) ---")
    if tools:
        lines.append(json.dumps(tools, ensure_ascii=False, indent=2))
    else:
        lines.append("לא חוברו שרתי MCP. אין Tools.")
    return "\n".join(lines).strip()


async def _ask_with_mcp(request: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request},
    ]
    steps = [f"1. המשתמשת ביקשה: {request}"]

    client = MCPClient()
    try:
        await client.connect_to_server(SERVER_PATH)
        steps.append("2. ה-Host הפעיל Client, וה-Client הריץ את server.py כתהליך נפרד (stdio).")

        mcp_tools = await client.list_tools()
        names = ", ".join(t.name for t in mcp_tools)
        steps.append(f"3. list_tools: השרת דיווח על {len(mcp_tools)} Tools: {names}.")
        steps.append("   ה-Host לא מכיר את הפונקציות האלה מראש – הוא שאל את השרת מה יש.")

        tools = [_to_llm_tool(t) for t in mcp_tools]
        steps.append("4. ה-Host צירף את רשימת ה-Tools לקריאה למודל.")

        answer = ""
        for round_no in range(1, MAX_ROUNDS + 1):
            response = await asyncio.to_thread(complete, messages, tools)
            msg = response.choices[0].message
            if not getattr(msg, "tool_calls", None):
                answer = msg.content or ""
                steps.append(f"{4 + round_no}. המודל ענה בטקסט – אין עוד Tools לבקש. סוף הלולאה.")
                break
            messages.append(_as_dict(msg))
            for call in msg.tool_calls:
                args = json.loads(call.function.arguments or "{}")
                steps.append(
                    f"{4 + round_no}. המודל בחר: {call.function.name}({json.dumps(args, ensure_ascii=False)})"
                    " — אנחנו לא ידענו מראש מה ייבחר."
                )
                result = await client.call_tool(call.function.name, args)
                steps.append(f"   ה-Client שלח call_tool לשרת. השרת הריץ והחזיר:\n   {result}")
                messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
        else:
            answer = "הלולאה הגיעה לתקרה בלי תשובה סופית."
            steps.append(f"{5 + MAX_ROUNDS}. עצרנו אחרי {MAX_ROUNDS} סבבים.")
    finally:
        await client.close()

    return {
        "answer": answer,
        "prompt": _prompt_text(messages, tools),
        "what_happened": "\n".join(steps),
        "notice": notice(),
    }


def ask(request: str, use_mcp: bool) -> dict:
    if use_mcp:
        return asyncio.run(_ask_with_mcp(request))

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request},
    ]
    response = complete(messages, None)
    steps = [
        f"1. המשתמשת ביקשה: {request}",
        "2. מצב: בלי MCP. ה-Host לא מחובר לשום שרת, ולכן אין Tools.",
        "3. המודל ענה מהידע הכללי שלו. אין חשבון, אין מדיניות, אין בדיקה.",
    ]
    return {
        "answer": response.choices[0].message.content or "",
        "prompt": _prompt_text(messages, None),
        "what_happened": "\n".join(steps),
        "notice": notice(),
    }
