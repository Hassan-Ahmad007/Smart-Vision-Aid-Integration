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