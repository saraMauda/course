# קובץ 4 – החלון בכיתה
# כותבות בקשה, בוחרות בלי MCP או עם MCP, ורואות תשובה + מה נשלח + מה קרה.

import gradio as gr

from ask_the_model import EXAMPLE_TEXT, EXAMPLES, ask


def send(text: str, mode: str):
    t = (text or "").strip() or EXAMPLE_TEXT
    try:
        result = ask(t, use_mcp=(mode == "עם MCP"))
    except Exception as exc:
        return str(exc), "", ""
    note = result["notice"]
    happened = result["what_happened"]
    if note:
        happened = f"({note})\n\n{happened}"
    return result["answer"], result["prompt"], happened


with gr.Blocks(
    title="שיעור 07",
    css=".gradio-container { direction: rtl; } footer { display: none !important; }",
) as demo:
    gr.Markdown("שיעור 07 — מבקשות, ורואות מי מספק את ה-Tools ומי מפעיל אותם.")
    text = gr.Textbox(label="בקשה", value=EXAMPLE_TEXT, lines=3)
    gr.Examples(
        label="דוגמאות — חיוב כפול, חיוב תקין, לא קשור",
        examples=[[item] for item in EXAMPLES],
        inputs=[text],
    )
    mode = gr.Radio(
        label="מה מחובר ל-Host",
        choices=["בלי MCP", "עם MCP"],
        value="בלי MCP",
    )
    btn = gr.Button("שלחי")
    answer = gr.Textbox(label="תשובה", lines=6)
    prompt_box = gr.Textbox(label="מה נשלח למודל (כולל ה-Tools)", lines=16)
    happened = gr.Textbox(label="מה קרה מאחורי הקלעים", lines=16)
    btn.click(send, inputs=[text, mode], outputs=[answer, prompt_box, happened])
    text.submit(send, inputs=[text, mode], outputs=[answer, prompt_box, happened])


if __name__ == "__main__":
    demo.launch(inbrowser=True, server_name="127.0.0.1")
