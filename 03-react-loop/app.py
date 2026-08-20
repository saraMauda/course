# קובץ 4 – החלון בכיתה
# כותבות הודעה, בוחרות אם לולאת ReAct רצה, ורואות תשובה + מה קרה.

import gradio as gr

from ask_the_model import ask
from prompt import EXAMPLE_TEXT, EXAMPLES


def send(text: str, mode: str):
    t = (text or "").strip() or EXAMPLE_TEXT
    try:
        result = ask(t, use_react=(mode == "עם ReAct"))
    except Exception as exc:
        return str(exc), "", ""
    note = result["notice"]
    happened = result["what_happened"]
    if note:
        happened = f"({note})\n\n{happened}"
    return result["answer"], result["prompt"], happened


with gr.Blocks(
    title="שיעור 03",
    css=".gradio-container { direction: rtl; } footer { display: none !important; }",
) as demo:
    gr.Markdown("שיעור 03 — כותבות הודעה, רואות תשובה, ורואות מה נשלח למודל.")
    text = gr.Textbox(label="הודעה", value=EXAMPLE_TEXT, lines=3)
    gr.Examples(
        label="דוגמאות — חיוב כפול, החזר בלי בדיקה, מחוץ לתחום",
        examples=[[item] for item in EXAMPLES],
        inputs=[text],
    )
    mode = gr.Radio(
        label="מה שולחים למודל",
        choices=["בלי לולאה", "עם ReAct"],
        value="בלי לולאה",
    )
    btn = gr.Button("שלחי")
    answer = gr.Textbox(label="תשובה", lines=8)
    prompt_box = gr.Textbox(label="מה נשלח למודל (הפרומפט)", lines=14)
    happened = gr.Textbox(label="מה קרה מאחורי הקלעים", lines=12)
    btn.click(send, inputs=[text, mode], outputs=[answer, prompt_box, happened])
    text.submit(send, inputs=[text, mode], outputs=[answer, prompt_box, happened])


if __name__ == "__main__":
    demo.launch(inbrowser=True, server_name="127.0.0.1")
