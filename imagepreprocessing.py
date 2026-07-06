import cv2
import numpy as np


def preprocess_versions(image):
    """
    Optimized preprocessing for printed documents
    (black text on white paper).
    Returns only the two most useful versions.
    """

    versions = []

    # Upscale image for better OCR
    h, w = image.shape[:2]
    image = cv2.resize(
        image,
        (w * 2, h * 2),
        interpolation=cv2.INTER_CUBIC
    )

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    versions.append(("gray", gray))

    # Remove camera noise
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # Normalize uneven lighting
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (35, 35))
    background = cv2.morphologyEx(
        denoised,
        cv2.MORPH_CLOSE,
        kernel
    )

    normalized = cv2.divide(
        denoised,
        background,
        scale=255
    )

    # Improve local contrast
    clahe = cv2.createCLAHE(
        clipLimit=3.0,
        tileGridSize=(8, 8)
    )

    contrast = clahe.apply(normalized)

    # Sharpen text edges
    blur = cv2.GaussianBlur(
        contrast,
        (0, 0),
        1.2
    )

    sharp = cv2.addWeighted(
        contrast,
        1.6,
        blur,
        -0.6,
        0
    )

    # Version 1 (Best for most printed pages)
    versions.append(("enhanced", sharp))

    # Version 2 (Fallback for low contrast pages)
    otsu = cv2.threshold(
        sharp,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    kernel2 = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (2, 2)
    )

    otsu = cv2.morphologyEx(
        otsu,
        cv2.MORPH_CLOSE,
        kernel2
    )

    versions.append(("otsu", otsu))

    return versions