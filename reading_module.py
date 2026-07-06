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
        blur_score = cv2.Laplacian(roi_gray, cv2.CV_64F).var()
        contrast_score = roi_gray.std()

        blur_score = min(blur_score / 350.0, 1.0)
        contrast_score = min(contrast_score / 70.0, 1.0)

        return 0.65 * blur_score + 0.35 * contrast_score

    def guide_user(self, quality, stable_count):
        if quality < 0.25:
            return "Move the page closer and improve lighting."
        if stable_count < self.stability_threshold:
            return "Hold the page steady."
        return "Hold steady."


def get_best_ocr_text(roi):

    best_text = ""
    best_score = 0

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    versions = preprocess_versions(roi)

    for name, processed in versions:

        text, score = extract_text_with_confidence(processed)

        print(f"\nVERSION: {name}")
        print(f"SCORE: {score}")
        print(f"TEXT: {text}")

        if score > best_score:
            best_score = score
            best_text = text

    return best_text, best_score

def process_capture(
    captured_roi,
    speak,
    stop_event,
    reading_busy,
    speech_queue,
    tts_busy
):
    """
    Runs OCR completely independent from
    the live camera loop.
    """

    if stop_event.is_set():
        return



    raw_text, ocr_score = get_best_ocr_text(captured_roi)

    print("\n====================")
    print("OCR SCORE:", ocr_score)
    print("RAW TEXT:")
    print(raw_text)
    print("====================\n")

    cv2.imwrite("captured_page.jpg", captured_roi)

    if stop_event.is_set():
        return

    if raw_text:

        cleaned = clean_text_with_llm(raw_text)

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

    # ---------------------------------------------------
    # Wait until ALL speech has finished
    # ---------------------------------------------------
    while (
            not stop_event.is_set()
            and (
                    not speech_queue.empty()
                    or tts_busy.is_set()
            )
    ):
        time.sleep(0.1)

    reading_busy.clear()

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


def run_reading(
    stop_event,
    sva_respond,
    camera_index,
    reading_busy,
    speech_queue,
    tts_busy
):
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



    scan_cooldown = False


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
            quality = scanner.calculate_quality(roi_gray)



            # Dynamic Box Color Feedback
            color = (0, 0, 255)
            if quality >= 0.35:
                color = (0, 255, 255)
            if quality >= 0.45 and scanner.stable_count >= 3:
                color = (0, 255, 0)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            cv2.putText(frame, "Place text/page inside this box", (x1, y1 - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color,
                        2)
            cv2.putText(frame, f"Quality: {quality:.2f} | Stable: {scanner.stable_count}/{scanner.stability_threshold}",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            now = time.time()

            if scan_cooldown:

                if reading_busy.is_set():

                    cv2.imshow("SVA - Reading Mode", frame)

                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        stop_event.set()

                    continue

                scan_cooldown = False

                scanner.perfect_start_time = None
                scanner.stable_count = 0

                speak("Ready for next text.", priority=2)



            elif (

                    not ocr_worker.is_busy()

                    and not reading_busy.is_set()

            ):
                if (
                        not reading_busy.is_set()
                        and now - last_guidance_time > 6
                ):
                    guide = scanner.guide_user(quality, scanner.stable_count)
                    if guide:
                        speak(guide, priority=3)
                    last_guidance_time = now

                if reading_busy.is_set():
                    cv2.imshow("SVA - Reading Mode", frame)

                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        stop_event.set()

                    continue

                # Balanced Threshold adjustments for real-world document feeds
                ready_to_capture = (quality >= 0.40 and scanner.stable_count >= scanner.stability_threshold)
                print(
                    f"Quality={quality:.2f} "
                    f"Stable={scanner.stable_count} "
                    f"Ready={ready_to_capture}"
                )
                if ready_to_capture:
                    if scanner.perfect_start_time is None:
                        print("START TIMER")
                        scanner.perfect_start_time = now
                        speak("Hold still. Capturing text.", priority=2)

                    elif now - scanner.perfect_start_time >= 0.5:
                        reading_busy.set()
                        captured_roi = roi.copy()

                        speak("Image captured. You may move the camera.", priority=2)

                        ocr_worker.start(
                            process_capture,
                            captured_roi,
                            speak,
                            stop_event,
                            reading_busy,
                            speech_queue,
                            tts_busy
                        )

                        scan_cooldown = True
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