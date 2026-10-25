"""שלבים 4-6: שליפה, פרומפט עם Guardrails, פלט JSON ו-Gradio."""
import json

import cohere
import numpy as np

import config

co = cohere.ClientV2(config.api_key())

with open("dataset.json", encoding="utf-8") as f:
    data = json.load(f)

matrix = np.load(config.VECTORS_FILE)


def retrieve(query: str, k: int = config.TOP_K) -> list[dict]:
    resp = co.embed(
        texts=[query],
        model=config.EMBED_MODEL,
        input_type="search_query",
        embedding_types=["float"],
    )
    q = np.array(resp.embeddings.float_[0], dtype=np.float32)
    q /= np.linalg.norm(q)
    sims = matrix @ q  # דמיון קוסינוס לכל שאלה במאגר
    top = np.argsort(-sims)[:k]
    return [
        {"question": data[i]["question"], "answer": data[i]["answer"], "score": round(float(sims[i]), 3)}
        for i in top
    ]


def build_prompt(query: str, results: list[dict]) -> str:
    context = "\n---\n".join(f"שאלה דומה: {r['question']}\nתשובה: {r['answer']}" for r in results)
    return f"""את/ה עוזר/ת שירות לקוחות. ענה על שאלת המשתמש בהתבסס *אך ורק* על ההקשר.

הקשר:
---
{context}
---

שאלה:
{query}

הוראות:
- ענה רק לפי ההקשר. אל תשתמש בידע קודם.
- אם ההקשר אינו מספיק, החזר בשדה answer בדיוק: "{config.NO_ANSWER}" ובשדה out_of_scope החזר true.
- היה תמציתי ואל תחזור על ההקשר מילה במילה.
- החזר JSON תקין בלבד במבנה:
{{"answer": "...", "out_of_scope": false, "confidence": "high|medium|low"}}"""


def answer(query: str) -> dict:
    results = retrieve(query)
    if not results or results[0]["score"] < config.SCORE_THRESHOLD:
        # Guardrail ראשון: מתחת לסף לא קוראים ל-LLM בכלל
        return {"answer": config.NO_ANSWER, "out_of_scope": True, "confidence": "low", "sources": results}
    resp = co.chat(
        model=config.CHAT_MODEL,
        messages=[{"role": "user", "content": build_prompt(query, results)}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    out = json.loads(resp.message.content[0].text)
    out["sources"] = results
    return out


def ui(query: str):
    r = answer(query)
    sources = "\n".join(f"{s['score']}  {s['question']}" for s in r["sources"])
    return r["answer"], r["out_of_scope"], sources, json.dumps(r, ensure_ascii=False, indent=2)


def main():
    import gradio as gr

    demo = gr.Interface(
        fn=ui,
        inputs=gr.Textbox(label="שאלה"),
        outputs=[
            gr.Textbox(label="תשובה"),
            gr.Checkbox(label="מחוץ לתחום?"),
            gr.Textbox(label="מקורות + ציון דמיון"),
            gr.Code(label="JSON מובנה", language="json"),
        ],
        title="Service Bot",
    )
    demo.launch()


if __name__ == "__main__":
    main()
