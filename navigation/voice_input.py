# import json
# import time
# import sounddevice as sd
# from vosk import Model, KaldiRecognizer

# MODEL_PATH = "model"
# SAMPLE_RATE = 16000
# SILENCE_TIMEOUT = 1.2

# model = Model(MODEL_PATH)


# def get_destination():
#     recognizer = KaldiRecognizer(model, SAMPLE_RATE)
#     recognizer.SetWords(True)

#     last_speech = time.time()
#     final_text = ""

#     print("Listening for destination...")

#     with sd.RawInputStream(
#         samplerate=SAMPLE_RATE,
#         blocksize=4000,
#         dtype="int16",
#         channels=1
#     ) as stream:

#         while True:
#             data, _ = stream.read(4000)

#             # IMPORTANT FIX: convert buffer → bytes
#             if recognizer.AcceptWaveform(bytes(data)):
#                 result = json.loads(recognizer.Result())
#                 text = result.get("text", "").strip()

#                 if text:
#                     final_text = text
#                     last_speech = time.time()
#             else:
#                 partial = json.loads(recognizer.PartialResult()).get("partial", "")
#                 if partial:
#                     last_speech = time.time()

#             # silence detection
#             if final_text and (time.time() - last_speech > SILENCE_TIMEOUT):
#                 return final_text

#             # safety escape
#             if time.time() - last_speech > 10 and final_text:
#                 # return final_text


import speech_recognition as sr
from voice_output import speak

def get_destination():
    r = sr.Recognizer()
    attempts = 0

    while attempts < 5:
        speak("Please say your destination")

        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=1)

            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=5)
            except:
                speak("I did not hear anything")
                attempts += 1
                continue

        try:
            text = r.recognize_google(audio)
            speak(f"You said {text}")
            return text

        except sr.UnknownValueError:
            speak("I did not understand, please repeat")
            attempts += 1

        except sr.RequestError:
            speak("Speech service not available")
            return None

    speak("Unable to get destination")
    return None
