import re
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"


def basic_clean_text(text):
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    text = text.replace("|", "I")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")
    return text.strip()


def clean_text_with_llm(raw_text):
    raw_text = basic_clean_text(raw_text)

    if len(raw_text) < 4:
        return ""

    prompt = f"""
Clean this OCR text for a blind user.

Rules:
- Fix obvious OCR mistakes.
- Do not add new information.
- Do not explain.
- Keep the original meaning.
- Make it easy to speak aloud.

OCR text:
{raw_text}

Cleaned text:
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=10
        )

        if response.status_code == 200:
            cleaned = response.json().get("response", "").strip()
            return basic_clean_text(cleaned)

    except Exception:
        pass

    return raw_text