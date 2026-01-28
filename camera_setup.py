import cv2
import pyttsx3
import speech_recognition as sr
import numpy as np
import time


class VisionAid:
    def __init__(self):
        # ---------- Voice ----------
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 175)

        # ---------- Speech Recognition ----------
        self.recognizer = sr.Recognizer()

        # ---------- Capture Box ----------
        self.box_w, self.box_h = 480, 320

        # ---------- Timing / State ----------
        self.last_guidance_time = 0
        self.perfect_start_time = None
        self.last_message = ""
        self.captured = False

    # --------------------------------------------------
    # SPEAK (ANTI-SPAM)
    # --------------------------------------------------
    def speak(self, text, force=False):
        if not force and text == self.last_message:
            return
        print(f"Assistant: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
        self.last_message = text

    # --------------------------------------------------
    # LISTEN COMMAND
    # --------------------------------------------------
    def listen_for_command(self):
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=3)
                command = self.recognizer.recognize_google(audio).lower()
                return "read" in command
        except:
            return False

    # --------------------------------------------------
    # TEXT PRESENCE (EDGE DENSITY)
    # --------------------------------------------------
    def text_presence_score(self, roi_gray):
        edges = cv2.Canny(roi_gray, 80, 160)
        density = np.sum(edges > 0) / edges.size
        return min(density * 4.0, 1.0)

    # --------------------------------------------------
    # SHARPNESS CHECK
    # --------------------------------------------------
    def sharpness_score(self, roi_gray):
        value = cv2.Laplacian(roi_gray, cv2.CV_64F).var()
        return min(value / 120.0, 1.0)

    # --------------------------------------------------
    # CENTER TEXT CHECK
    # --------------------------------------------------
    def center_score(self, roi_gray):
        h, w = roi_gray.shape
        center = roi_gray[h//4:3*h//4, w//4:3*w//4]
        edges = cv2.Canny(center, 80, 160)
        return min(np.sum(edges > 0) / edges.size * 5.0, 1.0)

    # --------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------
    def calculate_confidence(self, roi_gray):
        text_score = self.text_presence_score(roi_gray)
        sharp_score = self.sharpness_score(roi_gray)
        center_score = self.center_score(roi_gray)

        confidence = (
            0.45 * text_score +
            0.35 * sharp_score +
            0.20 * center_score
        )
        return confidence, text_score, sharp_score

    # --------------------------------------------------
    # GUIDANCE MESSAGE
    # --------------------------------------------------
    def get_guidance_message(self, text_score, sharp_score):
        if text_score < 0.25:
            return "Move closer to the text"
        if sharp_score < 0.35:
            return "Hold steady"
        return "Good"

    # --------------------------------------------------
    # CAMERA PROCESS
    # --------------------------------------------------
    def start_camera_process(self):
        cap = cv2.VideoCapture(0)
        self.speak("Camera started. Move slowly.", force=True)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            h, w, _ = frame.shape
            x1 = (w - self.box_w) // 2
            y1 = (h - self.box_h) // 2
            x2 = x1 + self.box_w
            y2 = y1 + self.box_h

            roi = frame[y1:y2, x1:x2]
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            confidence, text_score, sharp_score = self.calculate_confidence(roi_gray)

            # Draw box
            color = (0, 255, 0) if confidence > 0.75 else (0, 200, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Guidance (not spammy)
            if time.time() - self.last_guidance_time > 2:
                message = self.get_guidance_message(text_score, sharp_score)
                self.speak(message)
                self.last_guidance_time = time.time()

            # Auto Capture
            if confidence > 0.75:
                if self.perfect_start_time is None:
                    self.perfect_start_time = time.time()
                    self.speak("Hold steady", force=True)

                if time.time() - self.perfect_start_time >= 1.0:
                    cv2.imwrite("box_capture.jpg", roi)
                    self.speak("Captured successfully. Processing text.", force=True)
                    break
            else:
                self.perfect_start_time = None

            cv2.imshow("Vision Aid - Scanner", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    # --------------------------------------------------
    # RUN
    # --------------------------------------------------
    def run(self):
        self.speak("Vision system ready. Say read the text.", force=True)
        while True:
            if self.listen_for_command():
                self.start_camera_process()
                break


if __name__ == "__main__":
    VisionAid().run()
