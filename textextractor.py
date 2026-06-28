import pytesseract
import re
import numpy as np


def clean_ocr_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_text_with_confidence(image):
    configs = [
        "--oem 3 --psm 6",
        "--oem 3 --psm 11",
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
            score = avg_conf + length_bonus

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