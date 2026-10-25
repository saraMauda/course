# קובץ 5 – החלון בכיתה
# כותבות הודעה, בוחרות אם ה-Harness של LangChain פועל, ורואות תשובה + מה קרה.

import gradio as gr

from ask_the_model import ask
from prompt import EXAMPLE_TEXT, EXAMPLES, MODE_PLAIN, MODES


def send(text: str, mode: str):
    t = (text or "").strip() or EXAMPLE_TEXT
    try:
        result = ask(t, mode)
    except Exception as exc:
        return str(exc), "", ""
    happened = result["what_happened"]
    if result["notice"]:
        happened = f"({result['notice']})\n\n{happened}"
    return result["answer"], result["prompt"], happened


with gr.Blocks(
    title="שיעור 09",
    css=".gradio-container { direction: rtl; } footer { display: none !important; }",
) as demo:
    gr.Markdown("שיעור 09 — כותבות הודעה, רואות תשובה, ורואות מה ה-Harness עשה.")
    text = gr.Textbox(label="הודעה", value=EXAMPLE_TEXT, lines=3)
    gr.Examples(
        label="דוגמאות — שני כלים, כלי אחד, כשל כלי, חישוב, כלי חיצוני",
        examples=[[item] for item in EXAMPLES],
        inputs=[text],
    )
    mode = gr.Radio(label="מה מריצים", choices=MODES, value=MODE_PLAIN)
    btn = gr.Button("שלחי")
    answer = gr.Textbox(label="תשובה", lines=6)
    prompt_box = gr.Textbox(label="מה נשלח למודל (כולל הכלים)", lines=14)
    happened = gr.Textbox(label="מה קרה מאחורי הקלעים", lines=12)
    btn.click(send, inputs=[text, mode], outputs=[answer, prompt_box, happened])
    text.submit(send, inputs=[text, mode], outputs=[answer, prompt_box, happened])


if __name__ == "__main__":
    demo.launch(inbrowser=True, server_name="127.0.0.1")
