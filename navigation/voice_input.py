import queue
import sounddevice as sd
import json
from vosk import Model, KaldiRecognizer
from voice_output import speak

# path to your downloaded model folder
MODEL_PATH = "vosk-model-small-en-us-0.15"

q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))


def get_destination():
    try:
        model = Model(MODEL_PATH)
        recognizer = KaldiRecognizer(model, 16000)

        with sd.RawInputStream(
            samplerate=16000,
            blocksize=8000,
            dtype='int16',
            channels=1,
            callback=callback
        ):

            speak("Please say your destination")

            while True:
                data = q.get()

                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip()

                    if text:
                        speak(f"You said {text}")
                        return text

    except Exception as e:
        print("VOSK ERROR:", e)
        speak("Voice system failed")
        return None
