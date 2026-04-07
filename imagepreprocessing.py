import cv2
import numpy as np

def preprocess_fast(image):
    """
    High-accuracy OCR preprocessing for mobile camera documents
    """

    # 1️⃣ Resize EARLY (critical for small fonts)
    h, w = image.shape[:2]
    image = cv2.resize(image, (w*2, h*2), interpolation=cv2.INTER_CUBIC)

    # 2️⃣ Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 3️⃣ Strong denoise but preserve text
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # 4️⃣ Remove uneven lighting (background normalization)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (35, 35))
    background = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, kernel)
    normalized = cv2.divide(denoised, background, scale=255)

    # 5️⃣ Contrast boost (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8))
    contrast = clahe.apply(normalized)

    # 6️⃣ Mild sharpening (recover blurred edges)
    blur = cv2.GaussianBlur(contrast, (0, 0), 1.2)
    sharp = cv2.addWeighted(contrast, 1.6, blur, -0.6, 0)

    # 7️⃣ OCR-safe binarization (NOT harsh)
    thresh = cv2.threshold(
        sharp, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    # 8️⃣ Morphological cleanup (thicken characters slightly)
    kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    final = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel2)

    return final, "Image preprocessing Successfully done."
