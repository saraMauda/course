# קובץ 7 – החלון בכיתה
# כותבות הודעה, בוחרות מי שולט בזרימה, ורואות תשובה + כמה קריאות למודל + מה קרה.

import gradio as gr

from ask_the_model import ask
from prompt import EXAMPLE_TEXT, EXAMPLES, MODE_AGENT, MODES


def send(text: str, mode: str):
    t = (text or "").strip() or EXAMPLE_TEXT
    try:
        result = ask(t, mode)
    except Exception as exc:
        return str(exc), "", "", ""
    happened = result["what_happened"]
    if result["notice"]:
        happened = f"({result['notice']})\n\n{happened}"
    return result["answer"], result["control"], result["prompt"], happened


with gr.Blocks(
    title="שיעור 08",
    css=".gradio-container { direction: rtl; } footer { display: none !important; }",
) as demo:
    gr.Markdown("שיעור 08 — אותה הודעה, ארבע תבניות. רואות מי שולט, כמה זה עולה, ומה קרה.")
    text = gr.Textbox(label="הודעה", value=EXAMPLE_TEXT, lines=3)
    gr.Examples(
        label="דוגמאות — חיוב, הזמנה, מחוץ לתחום, חסר מספר",
        examples=[[item] for item in EXAMPLES],
        inputs=[text],
    )
    mode = gr.Radio(label="תבנית", choices=MODES, value=MODE_AGENT)
    btn = gr.Button("שלחי")
    answer = gr.Textbox(label="תשובה", lines=6)
    control = gr.Markdown()
    prompt_box = gr.Textbox(label="מה נשלח למודל (כל הקריאות)", lines=14)
    happened = gr.Textbox(label="מה קרה מאחורי הקלעים", lines=12)
    outputs = [answer, control, prompt_box, happened]
    btn.click(send, inputs=[text, mode], outputs=outputs)
    text.submit(send, inputs=[text, mode], outputs=outputs)


if __name__ == "__main__":
    demo.launch(inbrowser=True, server_name="127.0.0.1")
