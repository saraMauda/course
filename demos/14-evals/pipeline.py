# קובץ 4 – הצנרת שנבדקת
# אותה צנרת RAG משיעור 05, עם ארבעה "ידיות" שאפשר לשנות: סף, K, Guardrails.

from llm_client import complete
from prompt import build_prompt
from search import TOP_K, retrieve


def run_pipeline(question: str, config: dict) -> dict:
    ranked = retrieve(question, k=config.get("k", TOP_K))
    hits = [item for item in ranked if item["score"] >= config["threshold"]]
    prompt = build_prompt(question, hits, guardrails=config["guardrails"])
    response = complete([{"role": "user", "content": prompt}])
    return {
        "ranked": ranked,
        "hits": hits,
        "answer": (response.choices[0].message.content or "").strip(),
    }
