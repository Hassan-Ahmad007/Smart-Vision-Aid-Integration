import re
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:1b"


def basic_clean_text(text):
    """
    Remove obvious OCR artifacts before sending
    text to the LLM.
    """

    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r", "\n")

    # Remove OCR garbage symbols
    text = re.sub(r"[`~^]+", "", text)
    text = re.sub(r"[\\]+", " ", text)
    text = re.sub(r"[|]+", " ", text)

    # Normalize quotes
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")

    # Remove excessive punctuation
    text = re.sub(r"([.,;:!?]){2,}", r"\1", text)

    # Remove repeated hyphens
    text = re.sub(r"-{2,}", "-", text)

    # Remove extra spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Remove empty lines
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    return text.strip()


def clean_text_with_llm(raw_text):

    raw_text = basic_clean_text(raw_text)

    if len(raw_text) < 5:
        return ""

    prompt = f"""
You are an OCR correction engine for a Smart Vision Aid.

The following text was extracted from a PRINTED ENGLISH DOCUMENT using OCR.

Your task is ONLY to repair OCR mistakes.

Rules:

1. Never invent information.

2. Never rewrite sentences.

3. Never summarize.

4. Never explain anything.

5. Preserve the original meaning.

6. Preserve paragraphs.

7. Preserve numbered lists.

8. Preserve bullet lists.

9. Remove OCR garbage characters.

10. Remove isolated random symbols.

11. Remove isolated random letters that are clearly OCR noise.

12. Correct obvious spelling mistakes caused by OCR.

13. If a word is truncated, complete it ONLY if the surrounding sentence makes the completion highly certain.

Example:

OCR:
I would like to express my appreci for your support.

Output:
I would like to express my appreciation for your support.

Do NOT guess if uncertain.

Return ONLY the corrected text.

OCR TEXT:

{raw_text}

CORRECTED TEXT:
"""

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.05,
                    "top_p": 0.2,
                    "repeat_penalty": 1.15
                }
            },
            timeout=60
        )

        if response.status_code == 200:

            cleaned = response.json()["response"].strip()

            return basic_clean_text(cleaned)

    except Exception as e:

        print("LLM ERROR:", e)

    return raw_text