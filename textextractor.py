import pytesseract
import re
import pyttsx3
import threading
import queue

# ===================== TTS MANAGER =====================
class TTSManager:
    def __init__(self):
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        engine = pyttsx3.init()
        engine.setProperty("rate", 160)
        engine.setProperty("volume", 1.0)
        voices = engine.getProperty("voices")
        if voices:
            engine.setProperty("voice", voices[0].id)

        while True:
            text = self.queue.get()
            if text is None:
                break
            try:
                engine.say(text)
                engine.runAndWait()
            except RuntimeError:
                pass
            self.queue.task_done()

    def speak(self, text):
        if text and text.strip():
            print("SPEAK:", text)
            self.queue.put(text)

# Instantiate TTS
tts = TTSManager()

# ===================== OCR + TTS =====================
def extract_and_speak(preprocessed_image):
    """
    Extract text from a preprocessed image and speak it.
    Input: preprocessed_image - already prepared by your preprocessing module
    """
    if preprocessed_image is None:
        tts.speak("No image provided.")
        return ""

    # Use Tesseract on preprocessed image
    ocr_configs = ["--oem 3 --psm 6", "--oem 3 --psm 11", "--oem 3 --psm 3"]
    final_text = ""

    for config in ocr_configs:
        text = pytesseract.image_to_string(preprocessed_image, config=config)
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) >= 5:
            final_text = text
            break

    # Fallback: invert image if no text found
    if not final_text:
        import cv2
        inverted = cv2.bitwise_not(preprocessed_image)
        for config in ocr_configs:
            text = pytesseract.image_to_string(inverted, config=config)
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) >= 5:
                final_text = text
                break

    if not final_text:
        tts.speak("Unable to read text. Please improve lighting or move closer.")
        return ""

    # Speak sentence by sentence
    sentences = re.split(r'(?<=[.!?])\s+', final_text)
    for sentence in sentences:
        if len(sentence.strip()) > 3:
            tts.speak(sentence.strip())

    return final_text
