import json
import time
import threading
import subprocess
import pyaudio
import cv2

from queue import PriorityQueue
from vosk import Model, KaldiRecognizer

from vision_module import run_detection
from reading_module import run_reading
from currency_module import run_currency
from navigation.voice_input import get_destination
from navigation.route_guidance import run_guidance


def find_external_camera():
    print("Searching for external camera...")

    for index in range(1, 6):
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        time.sleep(1)

        if cap.isOpened():
            ret, frame = cap.read()

            if ret and frame is not None:
                cap.release()
                print(f"External camera found at index {index}")
                return index

        cap.release()

    print("No external camera detected.")
    return None


def is_camera_available(index):
    if index is None:
        return False

    for _ in range(3):
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        time.sleep(1)

        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()

            if ret and frame is not None:
                return True

        cap.release()
        time.sleep(1)

    return False


speech_queue = PriorityQueue()


def speech_worker():
    while True:
        priority, timestamp, text = speech_queue.get()

        if text is None:
            speech_queue.task_done()
            break

        try:
            print(f"\nSVA: {text}")

            text = str(text).replace('"', '')

            command = f'''
            Add-Type -AssemblyName System.Speech;
            $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer;
            $speak.Rate = 1;
            $speak.Volume = 100;
            $speak.Speak("{text}");
            '''

            process = subprocess.Popen(
                ["powershell", "-Command", command],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            process.wait()

        except Exception as e:
            print(f"TTS ERROR: {e}")

        finally:
            speech_queue.task_done()


speech_thread = threading.Thread(
    target=speech_worker,
    daemon=True
)

speech_thread.start()


def sva_respond(text, priority=2):
    if not text:
        return

    speech_queue.put((priority, time.time(), text))


def clear_speech_queue():
    while not speech_queue.empty():
        try:
            speech_queue.get_nowait()
            speech_queue.task_done()
        except:
            break


def kill_current_mode(
    active_thread,
    detection_thread,
    guidance_thread,
    currency_thread,
    stop_signal
):
    stop_signal.set()

    clear_speech_queue()

    for t in [
        active_thread,
        detection_thread,
        guidance_thread,
        currency_thread
    ]:
        if t and t.is_alive():
            t.join(timeout=2)

    cv2.destroyAllWindows()


if __name__ == "__main__":

    print("Loading Vosk model...")

    commands = [
        "activate",
        "smart vision aid",

        "switch to reading mode",
        "switch to detection mode",
        "switch to route guidance mode",
        "switch to currency mode",

        "reading mode",
        "detection mode",
        "guidance mode",
        "currency mode",

        "currency",
        "count currency",
        "money mode",

        "stop",
        "stop mode",

        "shutdown",
        "shut down",
        "exit system",

        "[unk]"
    ]

    grammar = json.dumps(commands)

    model = Model("model")
    rec = KaldiRecognizer(model, 16000, grammar)

    print("Vosk loaded successfully.")

    p = pyaudio.PyAudio()

    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=1024
    )

    stream.start_stream()

    print("Microphone initialized successfully.")

    system_active = False
    awaiting_mode_selection = False
    mode_running = False

    active_thread = None
    detection_thread = None
    guidance_thread = None
    currency_thread = None

    stop_signal = threading.Event()

    camera_index = find_external_camera()

    print("\n========================================")
    print("SYSTEM READY")
    print("Say: ACTIVATE")
    print("========================================\n")

    try:
        while True:

            try:
                data = stream.read(
                    1024,
                    exception_on_overflow=False
                )

            except Exception as e:
                print(f"MIC ERROR: {e}")
                continue

            if rec.AcceptWaveform(data):

                result = json.loads(rec.Result())
                text = result.get("text", "").strip()

                if not text:
                    continue

                if "[unk]" in text:
                    continue

                print(f"\nUSER: {text}")

                # =================================================
                # ACTIVATE
                # =================================================

                if not system_active:

                    if text == "activate":
                        system_active = True
                        awaiting_mode_selection = True

                        sva_respond(
                            "Smart Vision Aid activated. Please select your mode.",
                            priority=2
                        )

                        rec.Reset()

                    continue

                # =================================================
                # SHUTDOWN SYSTEM
                # =================================================

                if text in ["shutdown", "shut down", "exit system"]:

                    stop_signal.set()

                    kill_current_mode(
                        active_thread,
                        detection_thread,
                        guidance_thread,
                        currency_thread,
                        stop_signal
                    )

                    sva_respond(
                        "System shutting down. Goodbye.",
                        priority=0
                    )

                    break

                # =================================================
                # WAKE WORD / MODE CHANGE
                # =================================================

                if text == "smart vision aid":

                    kill_current_mode(
                        active_thread,
                        detection_thread,
                        guidance_thread,
                        currency_thread,
                        stop_signal
                    )

                    active_thread = None
                    detection_thread = None
                    guidance_thread = None
                    currency_thread = None

                    stop_signal = threading.Event()

                    mode_running = False
                    awaiting_mode_selection = True

                    sva_respond(
                        "Listening. Please select your mode.",
                        priority=2
                    )

                    rec.Reset()
                    continue

                # =================================================
                # STOP CURRENT MODE ONLY
                # =================================================

                if text in ["stop", "stop mode"]:

                    if mode_running:

                        kill_current_mode(
                            active_thread,
                            detection_thread,
                            guidance_thread,
                            currency_thread,
                            stop_signal
                        )

                        active_thread = None
                        detection_thread = None
                        guidance_thread = None
                        currency_thread = None

                        stop_signal = threading.Event()

                        mode_running = False
                        awaiting_mode_selection = True

                        sva_respond(
                            "Mode stopped. Please select your mode.",
                            priority=2
                        )

                        rec.Reset()
                        continue

                    else:

                        sva_respond(
                            "No mode is running. Say shutdown to close the system.",
                            priority=2
                        )

                        rec.Reset()
                        continue

                # =================================================
                # MODE SELECTION
                # =================================================

                if awaiting_mode_selection:

                    # =================================================
                    # DETECTION MODE
                    # =================================================

                    if text in [
                        "detection",
                        "detection mode",
                        "switch to detection mode"
                    ]:

                        if not is_camera_available(camera_index):
                            sva_respond(
                                "External camera is disconnected or unavailable. Please reconnect the camera and try again.",
                                priority=0
                            )
                            continue

                        kill_current_mode(
                            active_thread,
                            detection_thread,
                            guidance_thread,
                            currency_thread,
                            stop_signal
                        )

                        active_thread = None
                        detection_thread = None
                        guidance_thread = None
                        currency_thread = None

                        stop_signal = threading.Event()

                        awaiting_mode_selection = False

                        sva_respond(
                            "Starting object detection.",
                            priority=2
                        )

                        detection_thread = threading.Thread(
                            target=run_detection,
                            args=(stop_signal, sva_respond, camera_index),
                            daemon=True
                        )

                        detection_thread.start()

                        mode_running = True
                        rec.Reset()
                        continue

                    # =================================================
                    # READING MODE
                    # =================================================

                    elif text in [
                        "reading",
                        "reading mode",
                        "switch to reading mode"
                    ]:

                        if not is_camera_available(camera_index):
                            sva_respond(
                                "External camera is disconnected or unavailable. Please reconnect the camera and try again.",
                                priority=0
                            )
                            continue

                        kill_current_mode(
                            active_thread,
                            detection_thread,
                            guidance_thread,
                            currency_thread,
                            stop_signal
                        )

                        active_thread = None
                        detection_thread = None
                        guidance_thread = None
                        currency_thread = None

                        stop_signal = threading.Event()

                        awaiting_mode_selection = False

                        sva_respond(
                            "Starting reading mode.",
                            priority=2
                        )

                        active_thread = threading.Thread(
                            target=run_reading,
                            args=(stop_signal, sva_respond, camera_index),
                            daemon=True
                        )

                        active_thread.start()

                        mode_running = True
                        rec.Reset()
                        continue

                    # =================================================
                    # CURRENCY MODE
                    # =================================================

                    elif text in [
                        "currency",
                        "currency mode",
                        "switch to currency mode",
                        "count currency",
                        "money mode"
                    ]:

                        if not is_camera_available(camera_index):
                            sva_respond(
                                "External camera is disconnected or unavailable. Please reconnect the camera and try again.",
                                priority=0
                            )
                            continue

                        kill_current_mode(
                            active_thread,
                            detection_thread,
                            guidance_thread,
                            currency_thread,
                            stop_signal
                        )

                        active_thread = None
                        detection_thread = None
                        guidance_thread = None
                        currency_thread = None

                        stop_signal = threading.Event()

                        awaiting_mode_selection = False

                        sva_respond(
                            "Starting currency mode.",
                            priority=2
                        )

                        currency_thread = threading.Thread(
                            target=run_currency,
                            args=(stop_signal, sva_respond, camera_index),
                            daemon=True
                        )

                        currency_thread.start()

                        mode_running = True
                        rec.Reset()
                        continue

                    # =================================================
                    # GUIDANCE MODE
                    # =================================================

                    elif text in [
                        "guidance",
                        "guidance mode",
                        "switch to route guidance mode"
                    ]:

                        kill_current_mode(
                            active_thread,
                            detection_thread,
                            guidance_thread,
                            currency_thread,
                            stop_signal
                        )

                        active_thread = None
                        detection_thread = None
                        guidance_thread = None
                        currency_thread = None

                        stop_signal = threading.Event()

                        awaiting_mode_selection = False

                        sva_respond(
                            "Please say your destination.",
                            priority=1
                        )

                        time.sleep(1.5)

                        destination = get_destination(stream)

                        rec.Reset()

                        if destination:

                            print(f"\nDESTINATION: {destination}")

                            sva_respond(
                                f"Navigating to {destination}",
                                priority=1
                            )

                            if is_camera_available(camera_index):

                                detection_thread = threading.Thread(
                                    target=run_detection,
                                    args=(stop_signal, sva_respond, camera_index),
                                    daemon=True
                                )

                                detection_thread.start()

                            else:

                                sva_respond(
                                    "Camera is unavailable. Navigation will continue without obstacle detection.",
                                    priority=1
                                )

                            guidance_thread = threading.Thread(
                                target=run_guidance,
                                args=(
                                    stop_signal,
                                    sva_respond,
                                    destination
                                ),
                                daemon=True
                            )

                            guidance_thread.start()

                            mode_running = True
                            rec.Reset()
                            continue

                        else:

                            awaiting_mode_selection = True

                            sva_respond(
                                "I could not hear your destination.",
                                priority=1
                            )

                            rec.Reset()
                            continue


    except KeyboardInterrupt:
        print("\nKeyboard interrupt.")

    except Exception as e:
        print(f"\nSYSTEM ERROR: {e}")

    finally:

        print("\nCleaning up...")

        stop_signal.set()

        kill_current_mode(
            active_thread,
            detection_thread,
            guidance_thread,
            currency_thread,
            stop_signal
        )

        try:
            stream.stop_stream()
            stream.close()
        except:
            pass

        p.terminate()

        speech_queue.put((0, time.time(), None))

        print("System terminated.")