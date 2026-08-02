import cv2
import pytesseract
import numpy as np
import time
import threading

from imagepreprocessing import preprocess_versions
from textextractor import extract_text_with_confidence
from textcleaner import clean_text_with_llm

pytesseract.pytesseract.tesseract_cmd = r"C:\Users\hp\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"


class TextScanner:
    def __init__(self):
        self.box_w_ratio = 0.72
        self.box_h_ratio = 0.68

        self.stable_count = 0
        self.stability_threshold = 3
        self.perfect_start_time = None

    def get_reading_box(self, frame_w, frame_h):
        box_w = int(frame_w * self.box_w_ratio)
        box_h = int(frame_h * self.box_h_ratio)

        x1 = (frame_w - box_w) // 2
        y1 = (frame_h - box_h) // 2
        x2 = x1 + box_w
        y2 = y1 + box_h

        return x1, y1, x2, y2

    def check_stability(self, prev_gray, curr_gray, threshold=35):
        if prev_gray is None:
            return False

        diff = cv2.absdiff(prev_gray, curr_gray)

        motion = np.mean(diff)

        print(f"Motion={motion:.2f}")

        return motion < threshold

    def calculate_quality(self, roi_gray):
        # Blur score (higher = sharper)
        blur_score = cv2.Laplacian(
            roi_gray,
            cv2.CV_64F
        ).var()

        # Contrast score
        contrast_score = roi_gray.std()

        # Normalize
        blur_norm = min(blur_score / 350.0, 1.0)
        contrast_norm = min(contrast_score / 70.0, 1.0)

        quality = 0.65 * blur_norm + 0.35 * contrast_norm

        return quality, blur_score, contrast_score

    def guide_user(self, quality, stable_count):
        if quality < 0.25:
            return "Move the page closer and improve lighting."
        if stable_count < self.stability_threshold:
            return "Hold the page steady."
        return "Hold steady."


def get_all_ocr_results(roi):

    results = []

    versions = preprocess_versions(roi)

    for name, processed in versions:

        text, score = extract_text_with_confidence(processed)

        print(f"\nVERSION: {name}")
        print(f"SCORE: {score}")
        print(f"TEXT: {text}")

        results.append({
            "name": name,
            "text": text,
            "score": score
        })

    return results

def select_best_frame(frame_buffer):
    """
    Select the sharpest frame from the buffered candidates.

    Blur is given the highest priority because OCR accuracy depends
    much more on sharpness than on overall image quality.
    """

    if not frame_buffer:
        return None

    best_frame = None
    best_score = -1

    for frame in frame_buffer:

        score = (
            frame["blur"] * 0.70 +
            frame["quality"] * 300 * 0.20 +
            frame["contrast"] * 0.10
        )

        if score > best_score:
            best_score = score
            best_frame = frame

    print("\n===== BEST FRAME SELECTED =====")
    print(f"Blur      : {best_frame['blur']:.0f}")
    print(f"Quality   : {best_frame['quality']:.2f}")
    print(f"Contrast  : {best_frame['contrast']:.0f}")
    print("===============================\n")

    return best_frame["roi"]

def process_capture(
    captured_roi,
    speak,
    stop_event
):
    """
    Runs OCR completely independent from
    the live camera loop.
    """

    if stop_event.is_set():
        return



    ocr_results = get_all_ocr_results(captured_roi)

    prompt = ""

    for result in ocr_results:
        prompt += (
            f"\n\n"
            f"{result['name'].upper()} OCR\n"
            f"Confidence: {result['score']:.2f}\n"
            f"{result['text']}"
        )

    print("\n========== ALL OCR RESULTS ==========")
    print(prompt)
    print("=====================================\n")

    timestamp = int(time.time())
    cv2.imwrite(f"capture_{timestamp}.jpg", captured_roi)

    if stop_event.is_set():
        return

    if any(r["text"].strip() for r in ocr_results):

        cleaned = clean_text_with_llm(prompt)
        print("\n========== GEMINI OUTPUT ==========")
        print(cleaned)
        print("===================================\n")

        if cleaned:
            speak(cleaned, priority=2)

        else:
            speak(
                "Text was detected but could not be read clearly.",
                priority=2
            )

    else:

        speak(
            "Unable to read clearly. Please bring the page closer.",
            priority=2
        )

class OCRWorker:

    def __init__(self):
        self.thread = None
        self.processing = False

    def is_busy(self):
        return self.processing

    def start(self, target, *args):
        if self.processing:
            return False

        self.processing = True

        def runner():
            try:
                target(*args)
            finally:
                self.processing = False

        self.thread = threading.Thread(
            target=runner,
            daemon=True
        )

        self.thread.start()
        return True

    def stop(self):
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)


def run_reading(stop_event, sva_respond, camera_index):
    def speak(text, priority=2):
        if not stop_event.is_set():
            sva_respond(str(text), priority=priority)

    scanner = TextScanner()
    ocr_worker = OCRWorker()
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    time.sleep(1)

    if not cap.isOpened():
        cap.release()
        sva_respond("External camera is not available. Reading mode cannot start.", priority=0)
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    speak("Reading mode active. Bring the page in front of your face and keep it inside the box.")

    prev_gray = None
    last_guidance_time = 0

    # Best frame candidates collected during the capture window
    frame_buffer = []



    # Quality thresholds
    MIN_QUALITY = 0.40
    MIN_BLUR = 180
    MIN_CONTRAST = 25

    scan_cooldown = False
    cooldown_start = 0

    try:
        while not stop_event.is_set():
            ret, frame = cap.read()

            if not ret or frame is None:
                speak("Camera connection lost. Reading mode stopped.", priority=0)
                break

            frame_h, frame_w = frame.shape[:2]
            x1, y1, x2, y2 = scanner.get_reading_box(frame_w, frame_h)

            roi = frame[y1:y2, x1:x2].copy()
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            is_stable = scanner.check_stability(prev_gray, roi_gray)

            if is_stable:
                scanner.stable_count = min(scanner.stable_count + 1, scanner.stability_threshold)
            else:
                scanner.stable_count = max(scanner.stable_count - 2, 0)

            prev_gray = roi_gray.copy()
            quality, blur_score, contrast_score = scanner.calculate_quality(roi_gray)





            # Dynamic Box Color Feedback
            color = (0, 0, 255)
            if quality >= 0.35:
                color = (0, 255, 255)
            if quality >= 0.45 and scanner.stable_count >= 3:
                color = (0, 255, 0)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            cv2.putText(frame, "Place text/page inside this box", (x1, y1 - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color,
                        2)
            cv2.putText(
                frame,
                f"Q:{quality:.2f}  Blur:{blur_score:.0f}  Contrast:{contrast_score:.0f}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

            cv2.putText(
                frame,
                f"Stable: {scanner.stable_count}/{scanner.stability_threshold}",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

            now = time.time()

            if scan_cooldown:

                # Don't allow another capture while OCR is still running
                if ocr_worker.is_busy():
                    cv2.imshow("SVA - Reading Mode", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        stop_event.set()
                        break
                    continue

                if now - cooldown_start >= 3:
                    scan_cooldown = False

                    scanner.perfect_start_time = None
                    scanner.stable_count = 0
                    frame_buffer.clear()



                    speak("Ready for next text.", priority=2)


            elif not ocr_worker.is_busy():
                if now - last_guidance_time > 6:
                    guide = scanner.guide_user(quality, scanner.stable_count)
                    if guide:
                        speak(guide, priority=3)
                    last_guidance_time = now

                # Balanced Threshold adjustments for real-world document feeds
                ready_to_capture = (
                        quality >= MIN_QUALITY
                        and blur_score >= MIN_BLUR
                        and contrast_score >= MIN_CONTRAST
                        and scanner.stable_count >= scanner.stability_threshold
                )
                print(
                    f"Quality={quality:.2f} "
                    f"Stable={scanner.stable_count} "
                    f"Ready={ready_to_capture}"
                )
                if ready_to_capture:

                    if scanner.perfect_start_time is None:

                        print("START TIMER")

                        scanner.perfect_start_time = now

                        frame_buffer.clear()

                        speak("Hold still. Capturing text.", priority=2)

                    else:

                        frame_buffer.append({
                            "roi": roi.copy(),
                            "quality": quality,
                            "blur": blur_score,
                            "contrast": contrast_score
                        })
                    print(f"Collected {len(frame_buffer)} candidate frames")
                    if now - scanner.perfect_start_time >= 0.5:
                        captured_roi = select_best_frame(frame_buffer)

                        if captured_roi is None:
                            captured_roi = roi.copy()

                        speak("Image captured. You may move the camera.", priority=2)

                        print("\n===== CAPTURE INFO =====")
                        print(f"Frames Collected : {len(frame_buffer)}")
                        print("========================\n")

                        ocr_worker.start(
                            process_capture,
                            captured_roi,
                            speak,
                            stop_event
                        )

                        scan_cooldown = True
                        cooldown_start = time.time()
                else:
                    if scanner.perfect_start_time is not None:
                        print("RESET TIMER")

                    scanner.perfect_start_time = None

            cv2.imshow("SVA - Reading Mode", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                stop_event.set()
                break

    finally:
        ocr_worker.stop()
        cap.release()
        cv2.destroyAllWindows()
        sva_respond("Reading mode stopped. Goodbye.", priority=2)