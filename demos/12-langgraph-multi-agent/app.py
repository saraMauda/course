# קובץ 5 – החלון בכיתה
# בוחרות שלב, שולחות שאלה, ורואות מי עבדה, מתי, כמה זה לקח, ומה כל אחת כתבה ל-State.

import gradio as gr

from ask_the_model import ask, mermaid
from prompt import EXAMPLE_TEXT, EXAMPLES, STAGE_2, STAGES


def send(text: str, stage: str):
    t = (text or "").strip() or EXAMPLE_TEXT
    try:
        r = ask(t, stage)
        graph = mermaid(stage)
    except Exception as exc:
        return str(exc), "", "", "", "", "", ""
    steps = f"({r['notice']})\n\n{r['steps']}" if r["notice"] else r["steps"]
    return r["answer"], r["path"], r["summary"], steps, r["timeline"], r["state"], graph


def show_graph(stage: str):
    return mermaid(stage)


with gr.Blocks(
    title="שיעור 12",
    css=".gradio-container { direction: rtl; } footer { display: none !important; }",
) as demo:
    gr.Markdown("שיעור 12 — כמה מומחיות עובדות על שאלה אחת. רואות מי עבדה, מתי, וכמה זה עלה.")
    text = gr.Textbox(label="שאלה", value=EXAMPLE_TEXT, lines=2)
    gr.Examples(
        label="דוגמאות — שני מקורות, לולאה, כשל חלקי, אין מידע",
        examples=[[item] for item in EXAMPLES],
        inputs=[text],
    )
    stage = gr.Radio(label="שלב", choices=STAGES, value=STAGE_2)
    btn = gr.Button("שלחי")
    answer = gr.Textbox(label="תשובה", lines=4)
    path = gr.Markdown()
    summary = gr.Markdown()
    steps = gr.Textbox(label="מה כל node כתב ל-State", lines=12)
    timeline = gr.Textbox(label="ציר זמן (מי התחילה ומתי הסתיימה)", lines=8)
    state = gr.Textbox(label="ה-State בסוף", lines=6)
    graph = gr.Textbox(label="הגרף (Mermaid). אפשר להדביק ב-mermaid.live", lines=10)
    outputs = [answer, path, summary, steps, timeline, state, graph]
    btn.click(send, inputs=[text, stage], outputs=outputs)
    text.submit(send, inputs=[text, stage], outputs=outputs)
    stage.change(show_graph, inputs=[stage], outputs=[graph])


if __name__ == "__main__":
    demo.launch(inbrowser=True, server_name="127.0.0.1")
