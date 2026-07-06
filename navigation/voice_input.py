import speech_recognition as sr
import time


def get_destination(stream):

    recognizer = sr.Recognizer()

    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    print("\nNavigation MODE")
    print("Listening...")

    try:

        audio_bytes = b""

        start = time.time()

        while time.time() - start < 5:

            if stream.get_read_available() >= 1024:

                chunk = stream.read(
                    1024,
                    exception_on_overflow=False
                )

                audio_bytes += chunk

            else:
                time.sleep(0.01)

        print("Processing speech...")

        audio = sr.AudioData(
            audio_bytes,
            16000,
            2
        )

        text = recognizer.recognize_google(audio)

        print(f"Navigation system HEARD: {text}")

        return text

    except sr.UnknownValueError:

        print("Navigation system could not understand.")

        return None

    except sr.RequestError as e:

        print(f"Navigation system Error: {e}")

        return None

    except Exception as e:

        print(f"VOICE INPUT ERROR: {e}")

        return None