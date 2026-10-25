# קובץ 5 – החלון בכיתה
# שלב 1: מעלות מסמכים, הגרף נעצר, הנציגה מסמנת מה לאשר.
# שלב 2: שואלות שאלה, עם או בלי הגנות. אם יש הבטחת החזר והגנת HITL דלוקה, הגרף נעצר שוב.

import gradio as gr

import ask_the_model as core
from prompt import DEFENSES, EXAMPLE_TEXT, EXAMPLES, VARIANT_BLUNT, VARIANTS


def do_upload(variant: str):
    r = core.upload(variant)
    ids = [value for _, value in r["choices"]]
    return gr.update(choices=r["choices"], value=ids), r["table"], r["log"], "", "", "", ""


def do_approve(ids: list):
    r = core.approve(ids or [])
    return r["table"], r["log"]


def show_qa(r: dict, notice_text: str):
    steps = f"({notice_text})\n\n{r['steps']}" if notice_text else r["steps"]
    return r["answer"], r["status"], r["prompt"], steps


def do_ask(question: str, defenses: list):
    q = (question or "").strip() or EXAMPLE_TEXT
    return show_qa(core.ask(q, defenses or []), core.llm_notice())


def do_decide(approved: bool):
    return show_qa(core.decide(approved), core.llm_notice())


with gr.Blocks(
    title="שיעור 13",
    css=".gradio-container { direction: rtl; } footer { display: none !important; }",
) as demo:
    gr.Markdown("שיעור 13 — הגרף עוצר ומחכה לנציגה. ומה קורה כשמסמך מנסה לתת הוראות.")

    gr.Markdown("### שלב 1: העלאה ואישור מקורות (Upload → Review → Approve → Index)")
    variant = gr.Dropdown(label="סוג המסמך הזדוני (doc-3)", choices=VARIANTS, value=VARIANT_BLUNT)
    upload_btn = gr.Button("העלי 5 מסמכים")
    approve_ids = gr.CheckboxGroup(label="אשרי את המסמכים שייכנסו לאינדקס (⚠️ = סימון אוטומטי, לא החלטה)")
    approve_btn = gr.Button("אשרי את המסומנים ובני אינדקס")
    table = gr.Markdown()
    log = gr.Textbox(label="מה קרה בגרף", lines=8)

    gr.Markdown("### שלב 2: שאלה ללקוחה")
    question = gr.Textbox(label="שאלה", value=EXAMPLE_TEXT, lines=2)
    gr.Examples(label="דוגמאות", examples=[[e] for e in EXAMPLES], inputs=[question])
    defenses = gr.CheckboxGroup(label="הגנות פעילות", choices=DEFENSES, value=[])
    ask_btn = gr.Button("שאלי")
    status = gr.Markdown()
    with gr.Row():
        yes_btn = gr.Button("נציגה: אשרי שליחה")
        no_btn = gr.Button("נציגה: דחי")
    answer = gr.Textbox(label="התשובה שנשלחה ללקוחה", lines=3)
    prompt_box = gr.Textbox(label="מה נשלח למודל", lines=12)
    steps = gr.Textbox(label="מה קרה בגרף", lines=5)

    upload_btn.click(do_upload, inputs=[variant], outputs=[approve_ids, table, log, answer, status, prompt_box, steps])
    approve_btn.click(do_approve, inputs=[approve_ids], outputs=[table, log])
    qa_out = [answer, status, prompt_box, steps]
    ask_btn.click(do_ask, inputs=[question, defenses], outputs=qa_out)
    question.submit(do_ask, inputs=[question, defenses], outputs=qa_out)
    yes_btn.click(lambda: do_decide(True), outputs=qa_out)
    no_btn.click(lambda: do_decide(False), outputs=qa_out)


if __name__ == "__main__":
    demo.launch(inbrowser=True, server_name="127.0.0.1")
