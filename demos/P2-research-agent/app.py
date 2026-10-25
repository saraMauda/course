# החלון בכיתה: סוכן מחקר עם כלים, MCP, זיכרון וסיכום.
# שיחה ברצף. «שיחה חדשה» פותחת thread_id חדש.

import json

import gradio as gr

from agent import Research
from llm_client import notice
from tools import provider

EXAMPLES = [
    "שלום, שמי דנה.",
    "חפשי מה מצב סוכני ה-AI היום",
    "מה כתבו בהערות הצוות על LangGraph?",
    "חפשי מה ההבדל בין LangChain ל-LangGraph",
    "מה שמי?",
]

research = Research()
_epoch = [0]


def thread_id() -> str:
    return f"research-{_epoch[0]}"


async def send(text: str):
    t = (text or "").strip() or EXAMPLES[0]
    try:
        r = await research.ask(t, thread_id())
    except Exception as exc:
        return str(exc), "", "", ""
    structured = json.dumps(r["structured"].model_dump(), ensure_ascii=False, indent=2)
    status = f"**{research.mcp_status}** · חיפוש: `{provider()}`" + (f" · ({notice()})" if notice() else "")
    context = r["context"] + ("\n**הסיכום פעל:** ההיסטוריה הישנה הוחלפה בהודעת סיכום." if r["summarized"] else "")
    return r["answer"], structured, r["log"], status + "\n\n" + context


def reset():
    _epoch[0] += 1
    return "", "", "", f"שיחה חדשה. thread_id חדש: `{thread_id()}`"


with gr.Blocks(
    title="פרויקט 2",
    css=".gradio-container { direction: rtl; } footer { display: none !important; }",
) as demo:
    gr.Markdown("פרויקט 2 — סוכן מחקר: rewrite → search → scrape → MCP, עם זיכרון וסיכום.")
    text = gr.Textbox(label="הודעה", value=EXAMPLES[0], lines=2)
    gr.Examples(label="תסריט שיחה — שולחות לפי הסדר", examples=[[e] for e in EXAMPLES], inputs=[text])
    with gr.Row():
        btn = gr.Button("שלחי")
        new_btn = gr.Button("שיחה חדשה")
    answer = gr.Textbox(label="תשובה", lines=5)
    structured = gr.Textbox(label="ResearchAnswer (summary, sources, confidence)", lines=8)
    log = gr.Textbox(label="לוג tool calls: מה הופעל ולמה", lines=10)
    info = gr.Markdown()
    outputs = [answer, structured, log, info]
    btn.click(send, inputs=[text], outputs=outputs)
    text.submit(send, inputs=[text], outputs=outputs)
    new_btn.click(reset, outputs=outputs)


if __name__ == "__main__":
    demo.launch(inbrowser=True, server_name="127.0.0.1")
