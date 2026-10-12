# קובץ 4 – השליחה למודל
# בלי RAG: השאלה לבד, המודל עונה מהזיכרון.
# עם RAG: אחזור → פרומפט מועשר → המודל מנסח בגבולות ההקשר.

from llm_client import complete, embedding_model_name, model_name, notice
from prompt import build_prompt
from search import MIN_SCORE, TOP_K, retrieve


def _answer_of(response) -> str:
    return (response.choices[0].message.content or "").strip()


def ask(text: str, use_rag: bool) -> dict:
    question = (text or "").strip()
    steps = [f"1. המשתמשת שאלה: {question}"]

    if not use_rag:
        steps.append("2. מצב: בלי RAG. אין אחזור, אין הקשר.")
        steps.append(f"3. המודל ({model_name()}) עונה רק ממה שהוא זוכר.")
        steps.append("4. אין מקור, אין ציון, אין דרך לבדוק. זו תשובה חופשית.")
        response = complete([{"role": "user", "content": question}])
        return {
            "answer": _answer_of(response),
            "prompt": question,
            "what_happened": "\n".join(steps),
            "notice": notice(),
        }

    steps.append("2. מצב: עם RAG. קודם אחזור, אחר כך Generation.")
    ranked = retrieve(question)
    steps.append(
        f"3. Retrieval: embedding לשאלה ({embedding_model_name()}), "
        f"דירוג cosine מול שאלות המאגר, top-{TOP_K}:"
    )
    for item in ranked:
        steps.append(f"   - ציון {item['score']:.2f} — [{item['id']}] {item['question']}")

    hits = [item for item in ranked if item["score"] >= MIN_SCORE]
    steps.append(f"4. סף {MIN_SCORE:.2f}: {len(hits)} מקורות נכנסים להקשר.")
    if not hits:
        steps.append("5. אין הקשר. הפרומפט נשלח בכל זאת – ה-Guardrails אמורים לעצור המצאה.")
    else:
        ids = ", ".join(item["id"] for item in hits)
        steps.append(f"5. Augment: המקורות ({ids}) הוזרקו לפרומפט יחד עם הוראות Guardrails.")

    prompt = build_prompt(question, hits)
    response = complete([{"role": "user", "content": prompt}])
    steps.append(f"6. Generation: המודל ({model_name()}) ניסח תשובה מתוך ההקשר בלבד.")
    return {
        "answer": _answer_of(response),
        "prompt": prompt,
        "what_happened": "\n".join(steps),
        "notice": notice(),
    }
