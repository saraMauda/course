import os

from dotenv import load_dotenv

load_dotenv()

EMBED_MODEL = "embed-multilingual-v3.0"  # תומך עברית, 1024 ממדים
CHAT_MODEL = "command-a-03-2025"
TOP_K = 3
SCORE_THRESHOLD = 0.45  # לכייל לפי הציונים שרואים ב-scores.py
NO_ANSWER = "אני מצטער, אך המסמכים שסופקו אינם מכילים מספיק מידע כדי לענות על שאלה זו."
VECTORS_FILE = "faq.npy"


def api_key() -> str:
    key = os.environ.get("COHERE_API_KEY")
    if not key:
        raise SystemExit("חסר COHERE_API_KEY. צרו קובץ .env (ראו .env.example) והדביקו את המפתח.")
    return key
