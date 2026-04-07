import cv2
import pytesseract
import numpy as np
import pyttsx3
import speech_recognition as sr
import time

from sympy import true

from imagepreprocessing import preprocess_fast
from textextractor import extract_and_speak

# -------------------- TESSERACT PATH --------------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# -------------------- TTS MANAGER --------------------
class TTSManager:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 1.0)
        voices = self.engine.getProperty('voices')
        if voices:
            self.engine.setProperty('voice', voices[0].id)

    def speak(self, text):
        print(f"SPEAKING: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

tts_manager = TTSManager()
def speak(text): tts_manager.speak(text)

# -------------------- VOICE COMMAND --------------------
def listen_command(timeout=3, phrase_time_limit=3):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for command...")
        try:
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            return ""
    try:
        return r.recognize_google(audio).lower()
    except:
        return ""

# -------------------- TEXT SCANNER --------------------
class TextScanner:
    def __init__(self):
        self.box_w = 600
        self.box_h = 400
        self.stable_count = 0
        self.stability_threshold = 5   # reduced for faster capture
        self.perfect_start_time = None

    # ---------------- Camera selection ----------------
    def select_camera_source(self):
        for cam_id in [0, 1, 2]:
            cap = cv2.VideoCapture(cam_id)
            if cap.isOpened():
                cap.release()
                return cam_id
        return None

    # ---------------- Stability check ----------------
    def check_stability(self, prev_gray, curr_gray, threshold=15):
        if prev_gray is None:
            return False
        diff = cv2.absdiff(prev_gray, curr_gray)
        return np.mean(diff) < threshold

    # ---------------- Confidence calculation ----------------
    def calculate_confidence(self, roi_gray):
        try:
            # Upscale for better OCR on mobile
            roi_up = cv2.resize(roi_gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
            _, thresh = cv2.threshold(roi_up, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            data = pytesseract.image_to_data(thresh, config="--psm 6", output_type=pytesseract.Output.DICT)
            words = [w for w in data['text'] if w.strip() != ""]
            if len(words) == 0:
                return 0.0

            confs = []
            for c in data['conf']:
                try:
                    val = float(c)
                    if val > 0:  # ignore -1 or 0
                        confs.append(val)
                except:
                    continue

            avg_conf = np.mean(confs)/100.0 if confs else 0.5
            sharp_score = min(cv2.Laplacian(roi_up, cv2.CV_64F).var()/300.0, 1.0)
            return 0.6*avg_conf + 0.4*sharp_score
        except Exception as e:
            print("Confidence calculation error:", e)
            return 0.0

    # ---------------- Camera scanning ----------------
    def start_camera_process(self):
        camera_source = self.select_camera_source()
        if camera_source is None:
            speak("No camera found.")
            return False

        cap = cv2.VideoCapture(camera_source, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(camera_source)
        if not cap.isOpened():
            speak("Cannot access camera.")
            return False

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)

        speak("Camera started. Place text inside the green box and hold steady.")

        prev_gray = None
        captured = False
        last_announcement = time.time()
        best_roi = None
        best_conf = 0

        while not captured:
            ret, frame = cap.read()
            if not ret:
                speak("Camera error")
                break

            h, w = frame.shape[:2]
            # Adaptive box size
            box_w = min(self.box_w, w-20)
            box_h = min(self.box_h, h-20)
            x1 = (w - box_w)//2
            y1 = (h - box_h)//2
            x2 = x1 + box_w
            y2 = y1 + box_h

            roi = frame[y1:y2, x1:x2].copy()
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            # ---------------- Stability ----------------
            is_stable = self.check_stability(prev_gray, roi_gray)
            self.stable_count = min(self.stable_count+1, self.stability_threshold) if is_stable else max(self.stable_count-2,0)
            prev_gray = roi_gray.copy()

            # ---------------- Confidence ----------------
            confidence = self.calculate_confidence(roi_gray)

            # Keep the best frame
            if confidence > best_conf:
                best_conf = confidence
                best_roi = roi.copy()

            # ---------------- Draw box ----------------
            color = (0, 0, 255)
            if confidence > 0.35 and self.stable_count >= 3:
                color = (0,255,0)
            elif confidence > 0.2:
                color = (0,255,255)
            cv2.rectangle(frame, (x1,y1), (x2,y2), color, 3)
            cv2.putText(frame, f"Confidence: {confidence:.2f}  Stability: {self.stable_count}/{self.stability_threshold}",
                        (10,30), cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,255,255),2)

            # ---------------- Voice guidance ----------------
            if time.time()-last_announcement>5:
                if confidence<0.3:
                    speak("Move closer to text")
                elif confidence<0.5:
                    speak("Center text inside box")
                elif self.stable_count<self.stability_threshold:
                    speak("Hold camera steady")
                last_announcement = time.time()

            # ---------------- Auto-capture ----------------
            if (confidence > 0.35 and self.stable_count >= self.stability_threshold) or confidence > 0.6:
                if self.perfect_start_time is None:
                    self.perfect_start_time = time.time()
                    speak("Perfect! Hold still for capture.")
                elif time.time()-self.perfect_start_time >= 0.8:
                    if best_roi is not None:
                        cv2.imwrite("captured_text.jpg", best_roi)
                        speak("Image captured Successfully")
                        captured = True
                        break
            else:
                self.perfect_start_time = None

            cv2.imshow("Smart Text Scanner", frame)
            if cv2.waitKey(1)&0xFF == ord('q'):
                speak("Cancelling capture")
                break

        cap.release()
        cv2.destroyAllWindows()
        cv2.waitKey(1)
        return captured
# -------------------- PROCESS CAPTURED IMAGE --------------------
def process_captured_image():
    speak("Processing captured image for text...")
    image = cv2.imread("captured_text.jpg")
    if image is None:
        speak("Failed to load image")
        return
    processed_image, msg = preprocess_fast(image)
    cv2.imwrite("processed_image.jpg", processed_image)
    if msg:
        speak(msg)
    speak("Reading text now...")
    extract_and_speak(image)
    speak("Reading Text Completed")
    return true

# -------------------- MAIN PROGRAM --------------------
def main():
    speak("Smart Text Scanner Ready")
    time.sleep(1)
    speak("Say 'Read text' to begin or 'exit' to quit")

    while True:
        command = listen_command(timeout=5, phrase_time_limit=4)
        if not command:
            continue

        if "scan text" in command or "read text" in command or "scan" in command:
            speak("Starting text scanner...")
            scanner = TextScanner()
            captured = scanner.start_camera_process()
            if captured:
               success = process_captured_image()
               if success:
                speak("Scanning completed. Say 'Read text' for another document or 'exit' to quit.")
            else:
                speak("No text captured. Say 'read text' to try again or 'exit' to quit.")
        elif "exit" in command or "quit" in command or "stop" in command or "close" in command:
            speak("Closing Smart Text Scanner. Goodbye!")
            break
        else:
            # Only say this if command is wrong
            speak("Command not recognized. Please say 'scan text' to begin or 'exit' to quit.")

# -------------------- ENTRY POINT --------------------
if __name__=="__main__":
    try:
        main()
    except KeyboardInterrupt:
        speak("Program interrupted")
    finally:
        cv2.destroyAllWindows()
        print("System closed")