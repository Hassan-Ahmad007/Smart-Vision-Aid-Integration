import cv2
import pytesseract
import numpy as np
import time
import os

# Ensure these helper files are in the same directory
from imagepreprocessing import preprocess_fast
from textextractor import extract_text



# TESSERACT PATH (Keep your local path)
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\hp\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"


class TextScanner:
    def __init__(self):
        self.box_w = 600
        self.box_h = 400
        self.stable_count = 0
        self.stability_threshold = 5
        self.perfect_start_time = None

    def check_stability(self, prev_gray, curr_gray, threshold=15):
        if prev_gray is None: return False
        diff = cv2.absdiff(prev_gray, curr_gray)
        return np.mean(diff) < threshold

    def calculate_confidence(self, roi_gray):
        try:
            roi_up = cv2.resize(roi_gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
            _, thresh = cv2.threshold(roi_up, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            data = pytesseract.image_to_data(thresh, config="--psm 6", output_type=pytesseract.Output.DICT)
            words = [w for w in data['text'] if w.strip() != ""]
            if len(words) == 0: return 0.0

            confs = [float(c) for c in data['conf'] if str(c).replace('.', '').isdigit() and float(c) > 0]
            avg_conf = np.mean(confs) / 100.0 if confs else 0.5
            sharp_score = min(cv2.Laplacian(roi_up, cv2.CV_64F).var() / 300.0, 1.0)
            return 0.6 * avg_conf + 0.4 * sharp_score
        except:
            return 0.0




def run_reading(stop_event, sva_respond, camera_index):
    """Refactored Entry Point for the Manager"""

    def speak(text):
        sva_respond(str(text),priority=2)

    scanner = TextScanner()
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW) # Using your preferred Index 2
    time.sleep(1)

    if not cap.isOpened():
        cap.release()
        sva_respond(
            "External camera is not available. Reading mode cannot start.",
            priority=0
        )

        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Adjusted for stability
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    speak("Reading mode active. Place text inside the box.")

    prev_gray = None
    last_announcement = time.time()
    best_roi = None
    best_conf = 0

    try:
        while not stop_event.is_set():
            ret, frame = cap.read()

            if not ret or frame is None:
                sva_respond(
                    "Camera connection lost. Reading mode stopped.",
                    priority=0
                )

                break

            h, w = frame.shape[:2]
            x1, y1 = (w - scanner.box_w) // 2, (h - scanner.box_h) // 2
            x2, y2 = x1 + scanner.box_w, y1 + scanner.box_h

            roi = frame[y1:y2, x1:x2].copy()
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            # Stability & Confidence
            is_stable = scanner.check_stability(prev_gray, roi_gray)
            scanner.stable_count = min(scanner.stable_count + 1, scanner.stability_threshold) if is_stable else max(
                scanner.stable_count - 2, 0)
            prev_gray = roi_gray.copy()
            confidence = scanner.calculate_confidence(roi_gray)

            if confidence > best_conf:
                best_conf = confidence
                best_roi = roi.copy()

            # UI Feedback
            color = (0, 0, 255)
            if confidence > 0.35 and scanner.stable_count >= 3: color = (0, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)

            # Audio Guidance
            if time.time() - last_announcement > 5:
                if confidence < 0.3:
                    speak("Move closer")
                elif scanner.stable_count < scanner.stability_threshold:
                    speak("Hold steady")
                last_announcement = time.time()

            # Auto-Capture Logic
            if (confidence > 0.35 and scanner.stable_count >= scanner.stability_threshold) or confidence > 0.6:
                if scanner.perfect_start_time is None:
                    scanner.perfect_start_time = time.time()
                    speak("Hold still")
                elif time.time() - scanner.perfect_start_time >= 0.8:
                    if best_roi is not None:
                        cv2.imwrite("captured_text.jpg", best_roi)
                        speak("Captured. Processing.")

                        # Process logic (inline)
                        processed_image, _ = preprocess_fast(best_roi)
                        text = extract_text(processed_image)

                        if text:

                            speak(text)

                            speak("Reading completed. Ready for next scan.")

                        else:

                            speak(
                                "Unable to read text. "
                                "Please improve lighting or move closer."
                            )
                        # Reset for next scan
                        best_conf = 0
                        best_roi = None
                        scanner.perfect_start_time = None
            else:
                scanner.perfect_start_time = None

            cv2.imshow("SVA - Reading Mode", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

    finally:
        cap.release()
        cv2.destroyAllWindows()