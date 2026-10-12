# קובץ 6 – החלון בכיתה
# בוחרות גרסה של הצנרת, מריצות את כל ה-Golden set, ורואות ציונים + היסטוריה.

import gradio as gr

from evaluate import CONFIGS, HISTORY, run_eval
from llm_client import notice


def _mark(ok: bool) -> str:
    return "✅" if ok else "❌"


def run(config_name: str):
    try:
        result = run_eval(config_name)
    except Exception as exc:
        return str(exc), "", ""
    s = result["summary"]
    head = f"({notice()})\n\n" if notice() else ""
    summary = head + (
        f"**{s['config']}**\n\n"
        f"- אחזור (נשלף המקור הנכון): **{s['retrieval']}/{s['n_inside']}**\n"
        f"- תשובה נכונה (בתחום): **{s['answers']}/{s['n_inside']}**\n"
        f"- סירוב נכון (מחוץ לתחום): **{s['refusal']}/{s['n_outside']}**\n"
        f"- עברו בסך הכל: **{s['passed']}/{s['total']}**"
    )

    history = "| גרסה | אחזור | תשובות | סירוב | עברו |\n|---|---|---|---|---|\n"
    for h in HISTORY:
        history += (
            f"| {h['config']} | {h['retrieval']}/{h['n_inside']} | {h['answers']}/{h['n_inside']} "
            f"| {h['refusal']}/{h['n_outside']} | {h['passed']}/{h['total']} |\n"
        )

    details = "| שאלה | סוג | top-1 במאגר | אחזור | תשובה |\n|---|---|---|---|---|\n"
    for r in result["rows"]:
        details += (
            f"| {r['question']} | {r['kind']} | {r['top1']} | {_mark(r['retrieval_ok'])} "
            f"| {_mark(r['answer_ok'])} |\n"
        )
    return summary, history, details


with gr.Blocks(
    title="שיעור 14",
    css=".gradio-container { direction: rtl; } footer { display: none !important; }",
) as demo:
    gr.Markdown("שיעור 14 — משנות דבר אחד בצנרת, מריצות 12 שאלות, ורואות מה השתנה.")
    config = gr.Radio(
        label="גרסת הצנרת",
        choices=list(CONFIGS),
        value=list(CONFIGS)[0],
    )
    btn = gr.Button("הריצי בדיקה")
    summary = gr.Markdown()
    gr.Markdown("**כל הריצות עד עכשיו** (השוואה בין גרסאות)")
    history = gr.Markdown()
    gr.Markdown("**פירוט לפי שאלה**")
    details = gr.Markdown()
    btn.click(run, inputs=[config], outputs=[summary, history, details])


if __name__ == "__main__":
    demo.launch(inbrowser=True, server_name="127.0.0.1")
