import cv2
import numpy as np


def preprocess_versions(image):
    """
    Returns multiple OCR-ready versions.
    Better than using only one preprocessing style.
    """

    versions = []

    h, w = image.shape[:2]

    image = cv2.resize(
        image,
        (w * 2, h * 2),
        interpolation=cv2.INTER_CUBIC
    )

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (35, 35))
    background = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, kernel)
    normalized = cv2.divide(denoised, background, scale=255)

    clahe = cv2.createCLAHE(
        clipLimit=3.0,
        tileGridSize=(8, 8)
    )

    contrast = clahe.apply(normalized)

    blur = cv2.GaussianBlur(contrast, (0, 0), 1.2)
    sharp = cv2.addWeighted(contrast, 1.6, blur, -0.6, 0)

    versions.append(("gray_enhanced", sharp))

    otsu = cv2.threshold(
        sharp,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    otsu_clean = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel2)

    versions.append(("otsu", otsu_clean))
    versions.append(("inverted", cv2.bitwise_not(otsu_clean)))

    adaptive = cv2.adaptiveThreshold(
        sharp,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )

    versions.append(("adaptive", adaptive))

    return versions