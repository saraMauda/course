# קובץ 5 – החלון בכיתה
# בוחרות שלב בבנייה, שולחות הודעה, ורואות את המסלול בגרף ומה כל node כתב ל-State.

import gradio as gr

import ask_the_model
from ask_the_model import ask, mermaid
from prompt import EXAMPLE_TEXT, EXAMPLES, STAGE_2, STAGES


def send(text: str, stage: str):
    t = (text or "").strip() or EXAMPLE_TEXT
    try:
        result = ask(t, stage)
        graph = mermaid(stage)
    except Exception as exc:
        return str(exc), "", "", "", ""
    steps = result["steps"]
    if result["notice"]:
        steps = f"({result['notice']})\n\n{steps}"
    return result["answer"], f"**המסלול:** {result['path']}", steps, result["state"], graph


def show_graph(stage: str):
    return mermaid(stage)


def reset():
    ask_the_model.new_conversation()
    return "", "שיחה חדשה. thread_id חדש.", "", "", ""


with gr.Blocks(
    title="שיעור 11",
    css=".gradio-container { direction: rtl; } footer { display: none !important; }",
) as demo:
    gr.Markdown("שיעור 11 — בונות גרף שלב אחרי שלב, ורואות מה כל node כתב ל-State.")
    text = gr.Textbox(label="הודעה", value=EXAMPLE_TEXT, lines=2)
    gr.Examples(
        label="דוגמאות — חיוב, מדיניות, ושיחה (שם → מה שמי) בשלב 3",
        examples=[[item] for item in EXAMPLES],
        inputs=[text],
    )
    stage = gr.Radio(label="שלב", choices=STAGES, value=STAGE_2)
    with gr.Row():
        btn = gr.Button("שלחי")
        new_btn = gr.Button("שיחה חדשה")
    answer = gr.Textbox(label="תשובה", lines=4)
    path = gr.Markdown()
    steps = gr.Textbox(label="מה כל node כתב ל-State", lines=12)
    state = gr.Textbox(label="ה-State בסוף", lines=6)
    graph = gr.Textbox(label="הגרף (Mermaid). אפשר להדביק ב-mermaid.live", lines=10)
    outputs = [answer, path, steps, state, graph]
    btn.click(send, inputs=[text, stage], outputs=outputs)
    text.submit(send, inputs=[text, stage], outputs=outputs)
    new_btn.click(reset, outputs=outputs)
    stage.change(show_graph, inputs=[stage], outputs=[graph])


if __name__ == "__main__":
    demo.launch(inbrowser=True, server_name="127.0.0.1")
