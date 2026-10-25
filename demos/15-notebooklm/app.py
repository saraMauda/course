# קובץ 7 – החלון בכיתה
# upload → approve → chat. כל השיעורים בחלון אחד.

import gradio as gr

import chat
from prompt import COURSE_MAP, EXAMPLE_TEXT, EXAMPLES


def do_upload():
    r = chat.upload()
    ids = [value for _, value in r["choices"]]
    return gr.update(choices=r["choices"], value=ids), r["table"], r["log"], "", "", "", ""


def do_approve(ids: list):
    r = chat.approve(ids or [])
    return r["table"], r["log"]


def do_ask(question: str, web: bool):
    q = (question or "").strip() or EXAMPLE_TEXT
    try:
        r = chat.ask(q, bool(web))
    except Exception as exc:
        return str(exc), "", "", ""
    steps = f"({r['notice']})\n\n{r['steps']}" if r["notice"] else r["steps"]
    return r["answer"], r["citations"], steps, r["footer"]


def do_new():
    chat.reset()
    return gr.update(choices=[], value=[]), "", "מחברת חדשה. אינדקס ריק ו-thread_id חדש.", "", "", "", ""


with gr.Blocks(
    title="שיעור 15",
    css=".gradio-container { direction: rtl; } footer { display: none !important; }",
) as demo:
    gr.Markdown("שיעור 15 — מחברת קטנה מקצה לקצה: מקורות, אישור, גרף שיחה, ציטוטים וזיכרון.")

    gr.Markdown("### 1. מקורות (Source Pipeline + HITL)")
    upload_btn = gr.Button("העלי 4 מקורות")
    approve_ids = gr.CheckboxGroup(label="אשרי את המקורות שייכנסו למחברת (⚠️ = סימון אוטומטי, לא החלטה)")
    approve_btn = gr.Button("אשרי את המסומנים ובני אינדקס")
    table = gr.Markdown()
    log = gr.Textbox(label="מה קרה בצנרת המקורות", lines=5)

    gr.Markdown("### 2. שיחה (Chat Graph)")
    question = gr.Textbox(label="שאלה", value=EXAMPLE_TEXT, lines=2)
    gr.Examples(label="דוגמאות — מכוסה, מכוסה, מכוסה, מחוץ למקורות", examples=[[e] for e in EXAMPLES], inputs=[question])
    web = gr.Checkbox(label="הרחבה לאינטרנט (web_search)", value=False)
    with gr.Row():
        ask_btn = gr.Button("שאלי")
        new_btn = gr.Button("מחברת חדשה")
    answer = gr.Textbox(label="תשובה", lines=4)
    citations = gr.Markdown()
    steps = gr.Textbox(label="מה קרה בגרף (trace מקומי)", lines=7)
    footer = gr.Markdown()

    with gr.Accordion("מפת הקורס: איפה כל שיעור בדמו", open=False):
        gr.Markdown(COURSE_MAP)
    with gr.Accordion("גרף השיחה (Mermaid)", open=False):
        gr.Textbox(value=chat.mermaid(), label="אפשר להדביק ב-mermaid.live", lines=10)

    upload_btn.click(do_upload, outputs=[approve_ids, table, log, answer, citations, steps, footer])
    approve_btn.click(do_approve, inputs=[approve_ids], outputs=[table, log])
    ask_btn.click(do_ask, inputs=[question, web], outputs=[answer, citations, steps, footer])
    question.submit(do_ask, inputs=[question, web], outputs=[answer, citations, steps, footer])
    new_btn.click(do_new, outputs=[approve_ids, table, log, answer, citations, steps, footer])


if __name__ == "__main__":
    demo.launch(inbrowser=True, server_name="127.0.0.1")
