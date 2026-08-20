# קובץ 4 – החלון בכיתה
# כותבות שאלה, בוחרות אם לשלוח כלי, ורואות תשובה + מה קרה.

import gradio as gr

from ask_the_model import ask
from prompt import EXAMPLE_QUESTION


def send(question: str, mode: str):
    q = (question or "").strip() or EXAMPLE_QUESTION
    try:
        result = ask(q, use_tools=(mode == "עם כלי get_weather"))
    except Exception as exc:
        return str(exc), "", ""
    note = result["notice"]
    happened = result["what_happened"]
    if note:
        happened = f"({note})\n\n{happened}"
    return result["answer"], result["prompt"], happened


with gr.Blocks(
    title="שיעור 01",
    css=".gradio-container { direction: rtl; } footer { display: none !important; }",
) as demo:
    gr.Markdown("שיעור 01 — שואלות, רואות תשובה, ורואות מה נשלח למודל.")
    question = gr.Textbox(label="שאלה", value=EXAMPLE_QUESTION, lines=2)
    mode = gr.Radio(
        label="מה שולחים למודל",
        choices=["בלי כלים", "עם כלי get_weather"],
        value="בלי כלים",
    )
    btn = gr.Button("שלחי")
    answer = gr.Textbox(label="תשובה", lines=4)
    prompt_box = gr.Textbox(label="מה נשלח למודל (הפרומפט)", lines=14)
    happened = gr.Textbox(label="מה קרה מאחורי הקלעים", lines=12)
    btn.click(send, inputs=[question, mode], outputs=[answer, prompt_box, happened])
    question.submit(send, inputs=[question, mode], outputs=[answer, prompt_box, happened])


if __name__ == "__main__":
    demo.launch(inbrowser=True, server_name="127.0.0.1")
