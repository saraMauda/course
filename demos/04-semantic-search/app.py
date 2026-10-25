# קובץ 4 – החלון בכיתה
# כותבות שאילתה, בוחרות מילולי או סמנטי, ורואות תשובה + מה קרה.

import gradio as gr

from ask_the_model import ask
from catalog import EXAMPLE_TEXT, EXAMPLES


def send(text: str, mode: str):
    t = (text or "").strip() or EXAMPLE_TEXT
    try:
        result = ask(t, use_semantic=(mode == "חיפוש סמנטי"))
    except Exception as exc:
        return str(exc), "", "", ""
    note = result["notice"]
    happened = result["what_happened"]
    if note:
        happened = f"({note})\n\n{happened}"
    return result["answer"], result["prompt"], happened, result["embedding"]


with gr.Blocks(
    title="שיעור 04",
    css=".gradio-container { direction: rtl; } footer { display: none !important; }",
) as demo:
    gr.Markdown("שיעור 04 — כותבות שאילתה, רואות מקור מהמאגר, ורואות מה הוטמע.")
    text = gr.Textbox(label="שאילתה", value=EXAMPLE_TEXT, lines=3)
    gr.Examples(
        label="דוגמאות — ניסוח אחר, מילה משותפת, לא קשור",
        examples=[[item] for item in EXAMPLES],
        inputs=[text],
    )
    mode = gr.Radio(
        label="איך מחפשים במאגר",
        choices=["חיפוש מילולי", "חיפוש סמנטי"],
        value="חיפוש מילולי",
    )
    btn = gr.Button("שלחי")
    answer = gr.Textbox(label="תשובה", lines=8)
    prompt_box = gr.Textbox(label="מה הוטמע / מה חיפשו במאגר", lines=14)
    happened = gr.Textbox(label="מה קרה מאחורי הקלעים", lines=12)
    embedding = gr.Textbox(label="חישוב ה-embedding וה-cosine (רק בחיפוש סמנטי)", lines=18)
    btn.click(send, inputs=[text, mode], outputs=[answer, prompt_box, happened, embedding])
    text.submit(send, inputs=[text, mode], outputs=[answer, prompt_box, happened, embedding])


if __name__ == "__main__":
    demo.launch(inbrowser=True, server_name="127.0.0.1")
