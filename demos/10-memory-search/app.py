# קובץ 5 – החלון בכיתה
# שיחה אמיתית: שולחות כמה הודעות ברצף, ורואות מה נשמר ומה המודל קיבל בכל פעם.

import gradio as gr

import memory
from ask_the_model import ask
from prompt import EXAMPLE_TEXT, EXAMPLES, MODE_MEMORY, MODES


def send(text: str, mode: str):
    t = (text or "").strip() or EXAMPLE_TEXT
    try:
        result = ask(t, mode)
    except Exception as exc:
        return str(exc), "", "", ""
    happened = result["what_happened"]
    if result["notice"]:
        happened = f"({result['notice']})\n\n{happened}"
    return result["answer"], result["context"], result["prompt"], happened


def reset():
    memory.new_conversation()
    return "", "שיחה חדשה. thread_id חדש.", "", ""


with gr.Blocks(
    title="שיעור 10",
    css=".gradio-container { direction: rtl; } footer { display: none !important; }",
) as demo:
    gr.Markdown("שיעור 10 — שיחה ברצף. רואות מה נשמר, מה המודל קיבל, וכמה זה גדל.")
    text = gr.Textbox(label="הודעה", value=EXAMPLE_TEXT, lines=2)
    gr.Examples(
        label="תסריט שיחה — שולחות לפי הסדר, באותו מצב",
        examples=[[item] for item in EXAMPLES],
        inputs=[text],
    )
    mode = gr.Radio(label="זיכרון", choices=MODES, value=MODE_MEMORY)
    with gr.Row():
        btn = gr.Button("שלחי")
        new_btn = gr.Button("שיחה חדשה")
    answer = gr.Textbox(label="תשובה", lines=4)
    context = gr.Markdown()
    prompt_box = gr.Textbox(label="מה המודל קיבל בקריאה האחרונה (כל ההודעות)", lines=14)
    happened = gr.Textbox(label="מה קרה מאחורי הקלעים", lines=10)
    outputs = [answer, context, prompt_box, happened]
    btn.click(send, inputs=[text, mode], outputs=outputs)
    text.submit(send, inputs=[text, mode], outputs=outputs)
    new_btn.click(reset, outputs=outputs)


if __name__ == "__main__":
    demo.launch(inbrowser=True, server_name="127.0.0.1")
