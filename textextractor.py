import pytesseract
import re
import cv2


def extract_text(preprocessed_image):
    """
    Extract text from image and return it.
    NO speech here.
    """

    if preprocessed_image is None:
        return ""

    # =====================================================
    # OCR CONFIGS
    # =====================================================

    ocr_configs = [
        "--oem 3 --psm 6",
        "--oem 3 --psm 11",
        "--oem 3 --psm 3"
    ]

    final_text = ""

    # =====================================================
    # NORMAL OCR
    # =====================================================

    for config in ocr_configs:

        text = pytesseract.image_to_string(
            preprocessed_image,
            config=config
        )

        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) >= 5:

            final_text = text

            break

    # =====================================================
    # FALLBACK INVERTED IMAGE
    # =====================================================

    if not final_text:

        inverted = cv2.bitwise_not(preprocessed_image)

        for config in ocr_configs:

            text = pytesseract.image_to_string(
                inverted,
                config=config
            )

            text = re.sub(r'\s+', ' ', text).strip()

            if len(text) >= 5:

                final_text = text

                break

    return final_text