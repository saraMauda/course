# קובץ 4 – החלון בכיתה
# כותבות בקשה, בוחרות בלי Skills או עם Skills, ורואות תשובה + מה נשלח + מה קרה.

import gradio as gr

from ask_the_model import ask
from prompt import EXAMPLE_TEXT, EXAMPLES


def send(text: str, mode: str):
    t = (text or "").strip() or EXAMPLE_TEXT
    try:
        result = ask(t, use_skills=(mode == "עם Skills"))
    except Exception as exc:
        return str(exc), "", ""
    note = result["notice"]
    happened = result["what_happened"]
    if note:
        happened = f"({note})\n\n{happened}"
    return result["answer"], result["prompt"], happened


with gr.Blocks(
    title="שיעור 06",
    css=".gradio-container { direction: rtl; } footer { display: none !important; }",
) as demo:
    gr.Markdown("שיעור 06 — מבקשות, רואות מה נשלח למודל, ואיך skill נטען רק כשצריך.")
    text = gr.Textbox(label="בקשה", value=EXAMPLE_TEXT, lines=3)
    gr.Examples(
        label="דוגמאות — תלונה, סיכום מדיניות, לא קשור",
        examples=[[item] for item in EXAMPLES],
        inputs=[text],
    )
    mode = gr.Radio(
        label="מה שולחים למודל",
        choices=["בלי Skills", "עם Skills"],
        value="בלי Skills",
    )
    btn = gr.Button("שלחי")
    answer = gr.Textbox(label="תשובה", lines=8)
    prompt_box = gr.Textbox(label="מה נשלח למודל (הפרומפט)", lines=16)
    happened = gr.Textbox(label="מה קרה מאחורי הקלעים", lines=12)
    btn.click(send, inputs=[text, mode], outputs=[answer, prompt_box, happened])
    text.submit(send, inputs=[text, mode], outputs=[answer, prompt_box, happened])


if __name__ == "__main__":
    demo.launch(inbrowser=True, server_name="127.0.0.1")
