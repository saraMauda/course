import type { NotebookCell } from './py-notebook';

/** The code cells of project 1, taken from content/docs/projects/project-01-guide.md (steps 1-6). */
export const project1Cells: NotebookCell[] = [
  {
    id: 'install',
    title: 'תא 1: התקנה',
    code: String.raw`!pip install -q cohere gradio numpy`,
  },
  {
    id: 'connect',
    title: 'תא 2: חיבור',
    code: String.raw`import json
import numpy as np
from google.colab import userdata
import cohere

co = cohere.ClientV2(userdata.get("COHERE_API_KEY"))

EMBED_MODEL = "embed-multilingual-v3.0"   # תומך עברית
CHAT_MODEL = "command-a-03-2025"
print("מחובר")`,
  },
  {
    id: 'dataset',
    title: 'תא 3: המאגר',
    code: String.raw`with open("dataset.json", encoding="utf-8") as f:
    data = json.load(f)
questions = [item["question"] for item in data]
print(len(data), "זוגות. דוגמה:", data[0])`,
  },
  {
    id: 'embed',
    title: 'תא 4: Embeddings',
    code: String.raw`resp = co.embed(
    texts=questions,
    model=EMBED_MODEL,
    input_type="search_document",   # לשאלות שבמאגר
    embedding_types=["float"],
)
vectors = resp.embeddings.float_
print(len(vectors), "וקטורים, ממד", len(vectors[0]))`,
  },
  {
    id: 'save',
    title: 'תא 5: שמירת הווקטורים',
    code: String.raw`matrix = np.array(vectors, dtype=np.float32)
matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)   # נרמול: אורך 1 לכל וקטור
np.save("faq.npy", matrix)
print("נשמר faq.npy, צורה:", matrix.shape)`,
  },
  {
    id: 'retrieve',
    title: 'תא 6: שליפה',
    code: String.raw`def retrieve(query, k=3):
    r = co.embed(
        texts=[query],
        model=EMBED_MODEL,
        input_type="search_query",      # לשאילתה, שונה מ-search_document
        embedding_types=["float"],
    )
    q = np.array(r.embeddings.float_[0], dtype=np.float32)
    q /= np.linalg.norm(q)
    sims = matrix @ q                    # דמיון קוסינוס לכל השאלות במאגר
    top = np.argsort(-sims)[:k]          # k הגבוהים ביותר
    return [
        {"question": data[i]["question"],
         "answer": data[i]["answer"],
         "score": round(float(sims[i]), 3)}   # גבוה = דומה
        for i in top
    ]

for q in ["איבדתי את הפלאפון שלי", "כמה עולה לגלוש בחו\"ל", "מה מזג האוויר מחר?"]:
    print("\n>>", q)
    for r in retrieve(q):
        print(f"  {r['score']}  {r['question']}")`,
  },
  {
    id: 'answer',
    title: 'תא 7: פרומפט, Guardrails ופלט JSON',
    code: String.raw`SCORE_THRESHOLD = 0.45          # להחליף לפי הכיול שעשיתם
NO_ANSWER = "אני מצטער, אך המסמכים שסופקו אינם מכילים מספיק מידע כדי לענות על שאלה זו."

def build_prompt(query, results):
    context = "\n---\n".join(
        f"שאלה דומה: {r['question']}\nתשובה: {r['answer']}" for r in results
    )
    return f"""את/ה עוזר/ת שירות לקוחות. ענה על שאלת המשתמש בהתבסס *אך ורק* על ההקשר.

הקשר:
---
{context}
---

שאלה:
{query}

הוראות:
- ענה רק לפי ההקשר. אל תשתמש בידע קודם.
- אם ההקשר אינו מספיק, החזר בשדה answer בדיוק: "{NO_ANSWER}" ובשדה out_of_scope החזר true.
- היה תמציתי ואל תחזור על ההקשר מילה במילה.
- החזר JSON תקין בלבד במבנה:
{{"answer": "...", "out_of_scope": false, "confidence": "high|medium|low"}}"""

def answer(query):
    results = retrieve(query)
    if results[0]["score"] < SCORE_THRESHOLD:       # הגנה ראשונה: בלי לקרוא למודל
        return {"answer": NO_ANSWER, "out_of_scope": True,
                "confidence": "low", "sources": results}
    resp = co.chat(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": build_prompt(query, results)}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    out = json.loads(resp.message.content[0].text)
    out["sources"] = results
    return out

print(json.dumps(answer("באיזו שעה אתם פתוחים?"), ensure_ascii=False, indent=2))
print(json.dumps(answer("מי ניצח במונדיאל?"), ensure_ascii=False, indent=2))`,
  },
  {
    id: 'try',
    title: 'תא 8: ניסוי חופשי (במקום Gradio)',
    code: String.raw`QUESTION = "איך מבטלים חבילה?"   # לשנות ולהריץ שוב

r = answer(QUESTION)
print("תשובה:", r["answer"])
print("מחוץ לתחום?", r["out_of_scope"])
for s in r["sources"]:
    print(" ", s["score"], s["question"])`,
  },
];
