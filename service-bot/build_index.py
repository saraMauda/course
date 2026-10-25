"""שלבים 2-3: embeddings לשאלות ושמירתם כמטריצה מנורמלת. מריצים פעם אחת (ושוב רק כשה-dataset משתנה)."""
import json

import cohere
import numpy as np

import config

co = cohere.ClientV2(config.api_key())

with open("dataset.json", encoding="utf-8") as f:
    data = json.load(f)
questions = [item["question"] for item in data]

vectors = []
for start in range(0, len(questions), 90):  # ה-API מקבל עד 96 טקסטים בבקשה
    batch = questions[start:start + 90]
    resp = co.embed(
        texts=batch,
        model=config.EMBED_MODEL,
        input_type="search_document",
        embedding_types=["float"],
    )
    vectors.extend(resp.embeddings.float_)
print(f"נוצרו {len(vectors)} וקטורים, ממד {len(vectors[0])}")

matrix = np.array(vectors, dtype=np.float32)
matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)  # אחרי נרמול: מכפלה פנימית = דמיון קוסינוס
np.save(config.VECTORS_FILE, matrix)
print(f"נשמר {config.VECTORS_FILE}, צורה: {matrix.shape}")
