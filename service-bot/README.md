# Service Bot – שירות לקוחות סלולר (RAG עם Cohere + numpy + Gradio)

צ'אטבוט שעונה מתוך מאגר שאלות-תשובות, גם כשהניסוח שונה לגמרי, ומסרב לענות כשאין מידע.

## הרצה
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # ולהדביק COHERE_API_KEY בקובץ .env
python build_index.py       # פעם אחת: יוצר faq.npy
python scores.py            # כיול סף ה-out_of_scope
python bot.py               # פותח Gradio ב-http://127.0.0.1:7860
```

## קבצים
| קובץ | תפקיד |
|---|---|
| `dataset.json` | 36 זוגות question/answer |
| `config.py` | מודלים, ממד, סף, הודעת "אין מידע" |
| `build_index.py` | embeddings לשאלות + `faq.npy` (מטריצה מנורמלת) |
| `bot.py` | שליפה → סף → פרומפט עם Guardrails → JSON → Gradio |
| `scores.py` | כיול הסף |

## פלט מובנה (דוגמה)
```json
{"answer": "...", "out_of_scope": false, "confidence": "high", "sources": [{"question": "...", "answer": "...", "score": 0.71}]}
```

## מקרי בדיקה
(למלא אחרי ההרצה: 5 פגיעה טובה, 2 ניסוח חלופי, 1 מחוץ לתחום)
