from google import genai
import re
#Enter your gemini Api key
client = genai.Client(api_key="")




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


def clean_text_with_llm(ocr_results):

    prompt = f"""
You are an OCR reconstruction assistant.

The following text comes from three OCR preprocessing methods
applied to the SAME image.

Each OCR version recognizes different words correctly.

Compare all versions carefully and reconstruct the original
text as accurately as possible.

- The three OCR outputs come from the SAME image.
- Different versions may recognize different words correctly.
- Prefer words that are consistent across multiple versions.
- If only one version contains a word but it clearly fits the surrounding context, you may use it.
- Remove obvious OCR garbage such as random symbols or repeated nonsense fragments.
- Preserve the original paragraph order.
- Do not add information that is not present in any OCR version.

Rules:

- Merge information from all versions.
- Correct obvious OCR mistakes.
- Do not summarize.
- Do not paraphrase.
- Do not invent new information.
- Preserve formatting as much as possible.
- Return only the reconstructed text.

OCR Results:

{ocr_results}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:

        print("Gemini Error:", e)
        return None