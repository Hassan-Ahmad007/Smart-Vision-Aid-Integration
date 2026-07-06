import pytesseract
import re
import numpy as np


def clean_ocr_text(text):
    """
    Removes common OCR artifacts while preserving
    genuine punctuation and document structure.
    """

    if not text:
        return ""

    # Normalize spaces
    text = re.sub(r"\s+", " ", text)

    # Remove common OCR junk symbols
    text = re.sub(r"[\\|`~]+", " ", text)

    # Remove repeated punctuation
    text = re.sub(r"([.,;:!?]){2,}", r"\1", text)

    # Remove isolated single-character noise
    text = re.sub(r"\b[^\w\s]\b", " ", text)

    # Remove isolated random letters
    text = re.sub(r"\b[a-zA-Z]\b", " ", text)

    # Remove repeated spaces again
    text = re.sub(r"\s{2,}", " ", text)

    return text.strip()

def extract_text_with_confidence(image):
    configs = [
        "--oem 3 --psm 6",
        "--oem 3 --psm 3"
    ]

    best_text = ""
    best_score = 0

    for config in configs:
        try:
            data = pytesseract.image_to_data(
                image,
                config=config,
                output_type=pytesseract.Output.DICT
            )

            words = []
            confs = []

            for word, conf in zip(data["text"], data["conf"]):
                word = word.strip()

                try:
                    conf = float(conf)
                except:
                    conf = -1

                if word:
                    words.append(word)

                    if conf > 0:
                        confs.append(conf)

            text = clean_ocr_text(" ".join(words))

            if not text:
                continue

            avg_conf = np.mean(confs) if confs else 0
            length_bonus = min(len(text) / 120, 1) * 20
            word_count = len(words)

            score = (
                    avg_conf * 0.75 +
                    min(word_count, 120) * 0.25
            )

            print("CONFIG:", config)
            print("TEXT:", text)
            print("CONF:", avg_conf)

            if score > best_score:
                best_score = score
                best_text = text


        except Exception as e:

            print("TESSERACT ERROR:", e)

            continue

    return best_text, best_score