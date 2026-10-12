# קובץ 5 – החלון בכיתה
# כותבות שאלה, בוחרות בלי RAG או עם RAG, ורואות תשובה + פרומפט + מה קרה.

import gradio as gr

from ask_the_model import ask
from catalog import EXAMPLE_TEXT, EXAMPLES


def send(text: str, mode: str):
    t = (text or "").strip() or EXAMPLE_TEXT
    try:
        result = ask(t, use_rag=(mode == "עם RAG"))
    except Exception as exc:
        return str(exc), "", ""
    note = result["notice"]
    happened = result["what_happened"]
    if note:
        happened = f"({note})\n\n{happened}"
    return result["answer"], result["prompt"], happened


with gr.Blocks(
    title="שיעור 05",
    css=".gradio-container { direction: rtl; } footer { display: none !important; }",
) as demo:
    gr.Markdown("שיעור 05 — שואלות, רואות מה נשלח למודל, ומה בא מהמאגר.")
    text = gr.Textbox(label="שאלה", value=EXAMPLE_TEXT, lines=3)
    gr.Examples(
        label="דוגמאות — ניסוח אחר, מדיניות, לא קשור",
        examples=[[item] for item in EXAMPLES],
        inputs=[text],
    )
    mode = gr.Radio(
        label="איך עונים",
        choices=["בלי RAG", "עם RAG"],
        value="בלי RAG",
    )
    btn = gr.Button("שלחי")
    answer = gr.Textbox(label="תשובה", lines=6)
    prompt_box = gr.Textbox(label="מה נשלח למודל", lines=16)
    happened = gr.Textbox(label="מה קרה מאחורי הקלעים", lines=12)
    btn.click(send, inputs=[text, mode], outputs=[answer, prompt_box, happened])
    text.submit(send, inputs=[text, mode], outputs=[answer, prompt_box, happened])


if __name__ == "__main__":
    demo.launch(inbrowser=True, server_name="127.0.0.1")
