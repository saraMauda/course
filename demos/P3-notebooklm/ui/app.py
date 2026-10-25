# ui/app.py – החלון
# מקורות (data/ + טקסט מודבק) → סקירה ואישור (HITL) → שיחה עם ציטוטים → Evals.
# הרצה:  python ui/app.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # כדי ש-import chat יעבוד מכל תיקייה

import gradio as gr

import chat
import eval as ev
from prompt import COURSE_MAP, EXAMPLES


def do_load():
    n = chat.load_data()
    return chat.sources_table(), f"נטענו {n} מקורות מ-data/ (כולם pending). לחצי «התחילי סקירה»."


def do_add(title: str, text: str):
    if not (text or "").strip():
        return chat.sources_table(), "הדביקי טקסט קודם."
    sid = chat.add_text(title, text)
    return chat.sources_table(), f"נוסף המקור {sid} (pending). לחצי «התחילי סקירה»."


def do_review():
    r = chat.begin_review()
    ids = [value for _, value in r["choices"]]
    return gr.update(choices=r["choices"], value=ids), chat.sources_table(), r["log"]


def do_approve(ids: list):
    r = chat.approve(ids or [])
    return gr.update(choices=[], value=[]), chat.sources_table(), r["log"]


def do_ask(question: str, web: bool):
    q = (question or "").strip() or EXAMPLES[0]
    try:
        r = chat.ask(q, bool(web))
    except Exception as exc:
        return str(exc), "", "", ""
    trace = f"({r['notice']})\n\n{r['trace']}" if r["notice"] else r["trace"]
    return r["answer"], r["citations"], trace, r["footer"]


def do_new_session():
    chat.new_session()
    return "", "", "", f"שיחה חדשה: thread_id `{chat.thread_id()}`. אותם מקורות, בלי זיכרון."


def do_new_notebook():
    chat.reset_notebook()
    return chat.sources_table(), "", "", "", f"מחברת חדשה `{chat.notebook_id()}`. אינדקס ריק.", gr.update(choices=[], value=[])


def do_eval():
    return ev.table(ev.run_eval())


with gr.Blocks(
    title="פרויקט 3",
    css=".gradio-container { direction: rtl; } footer { display: none !important; }",
) as demo:
    gr.Markdown("פרויקט 3 — מחברת מקצה לקצה: מקורות, אישור, גרף שיחה, ציטוטים, זיכרון, trace ובדיקות.")

    gr.Markdown("### 1. מקורות")
    with gr.Row():
        load_btn = gr.Button("טעני את קבצי data/")
        review_btn = gr.Button("התחילי סקירה (HITL)")
    with gr.Accordion("הוספת מקור מטקסט מודבק", open=False):
        add_title = gr.Textbox(label="כותרת")
        add_text = gr.Textbox(label="טקסט", lines=3)
        add_btn = gr.Button("הוסיפי כ-pending")
    approve_ids = gr.CheckboxGroup(label="אשרי את המקורות שייכנסו למחברת (⚠️ = סימון אוטומטי, לא החלטה)")
    approve_btn = gr.Button("אשרי את המסומנים ובני אינדקס")
    table = gr.Markdown(chat.sources_table())
    log = gr.Textbox(label="מה קרה בצנרת המקורות", lines=5)

    gr.Markdown("### 2. שיחה")
    question = gr.Textbox(label="שאלה", value=EXAMPLES[0], lines=2)
    gr.Examples(label="דוגמאות", examples=[[e] for e in EXAMPLES], inputs=[question])
    web = gr.Checkbox(label="הרחבה לאינטרנט (web_search / scrape_url)", value=False)
    with gr.Row():
        ask_btn = gr.Button("שאלי")
        session_btn = gr.Button("שיחה חדשה (אותם מקורות)")
        notebook_btn = gr.Button("מחברת חדשה")
    answer = gr.Textbox(label="תשובה", lines=4)
    citations = gr.Markdown()
    trace = gr.Textbox(label="מה קרה בגרף (trace מקומי)", lines=7)
    footer = gr.Markdown()

    gr.Markdown("### 3. בדיקות (Evals)")
    eval_btn = gr.Button("הריצי 8 מקרי בדיקה")
    eval_out = gr.Markdown()

    with gr.Accordion("מפת הקורס: איפה כל שיעור בפרויקט", open=False):
        gr.Markdown(COURSE_MAP)
    with gr.Accordion("גרף השיחה (Mermaid)", open=False):
        gr.Textbox(value=chat.mermaid(), label="אפשר להדביק ב-mermaid.live", lines=12)

    load_btn.click(do_load, outputs=[table, log])
    add_btn.click(do_add, inputs=[add_title, add_text], outputs=[table, log])
    review_btn.click(do_review, outputs=[approve_ids, table, log])
    approve_btn.click(do_approve, inputs=[approve_ids], outputs=[approve_ids, table, log])
    ask_btn.click(do_ask, inputs=[question, web], outputs=[answer, citations, trace, footer])
    question.submit(do_ask, inputs=[question, web], outputs=[answer, citations, trace, footer])
    session_btn.click(do_new_session, outputs=[answer, citations, trace, footer])
    notebook_btn.click(do_new_notebook, outputs=[table, answer, citations, trace, footer, approve_ids])
    eval_btn.click(do_eval, outputs=[eval_out])


if __name__ == "__main__":
    demo.launch(inbrowser=True, server_name="127.0.0.1")
