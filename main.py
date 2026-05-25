import json
import time
import threading
import subprocess
import pyaudio
from queue import PriorityQueue

from vosk import Model, KaldiRecognizer

# =========================================================
# MODULES
# =========================================================

from vision_module import run_detection
from reading_module import run_reading
from navigation.voice_input import get_destination
from navigation.route_guidance import run_guidance

# =========================================================
# SPEECH PRIORITY QUEUE
# =========================================================

speech_queue = PriorityQueue()

# PRIORITIES
# 0 = emergency
# 1 = navigation
# 2 = system
# 3 = detection

# =========================================================
# SPEECH WORKER
# =========================================================

def speech_worker():

    while True:

        priority, text = speech_queue.get()

        if text is None:
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
                [
                    "powershell",
                    "-Command",
                    command
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # WAIT UNTIL SPEECH FINISHES
            process.wait()

        except Exception as e:

            print(f"TTS ERROR: {e}")

        finally:

            speech_queue.task_done()


# =========================================================
# START SPEECH THREAD
# =========================================================

speech_thread = threading.Thread(
    target=speech_worker,
    daemon=True
)

speech_thread.start()

# =========================================================
# CENTRAL SPEECH FUNCTION
# =========================================================

def sva_respond(text, priority=2):

    if not text:
        return

    speech_queue.put((priority, text))


# =========================================================
# STOP CURRENT MODE
# =========================================================

def kill_current_mode(
    active_thread,
    detection_thread,
    guidance_thread,
    stop_signal
):

    stop_signal.set()

    for t in [active_thread, detection_thread, guidance_thread]:

        if t and t.is_alive():

            t.join(timeout=2)


# =========================================================
# MAIN PROGRAM
# =========================================================

if __name__ == "__main__":

    # =====================================================
    # LOAD VOSK
    # =====================================================

    print("Loading Vosk model...")

    commands = [
        "activate",
        "smart vision aid",
        "switch to reading mode",
        "switch to detection mode",
        "switch to route guidance mode",
        "reading mode",
        "detection mode",
        "guidance mode",
        "stop",
        "[unk]"
    ]

    grammar = json.dumps(commands)

    model = Model("model")

    rec = KaldiRecognizer(model, 16000, grammar)

    print("Vosk loaded successfully.")

    # =====================================================
    # MICROPHONE
    # =====================================================

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

    # =====================================================
    # STATES
    # =====================================================

    system_active = False

    awaiting_mode_selection = False

    active_thread = None
    detection_thread = None
    guidance_thread = None

    stop_signal = threading.Event()

    # =====================================================
    # STARTUP
    # =====================================================

    print("\n========================================")
    print("SYSTEM READY")
    print("Say: ACTIVATE")
    print("========================================\n")

    # =====================================================
    # MAIN LOOP
    # =====================================================

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
                # ACTIVATE SYSTEM
                # =================================================

                if not system_active:

                    if "activate" in text:

                        system_active = True

                        awaiting_mode_selection = True

                        sva_respond(
                            "Smart Vision Aid activated. Please select your mode.",
                            priority=2
                        )

                        rec.Reset()

                    continue

                # =================================================
                # INTERRUPT ASSISTANT
                # =================================================

                if "smart vision aid" in text:

                    kill_current_mode(
                        active_thread,
                        detection_thread,
                        guidance_thread,
                        stop_signal
                    )

                    active_thread = None
                    detection_thread = None
                    guidance_thread = None

                    awaiting_mode_selection = True

                    sva_respond(
                        "Listening. Please select your mode.",
                        priority=2
                    )

                    rec.Reset()

                    continue

                # =================================================
                # STOP SYSTEM
                # =================================================

                if "stop" in text:

                    stop_signal.set()

                    kill_current_mode(
                        active_thread,
                        detection_thread,
                        guidance_thread,
                        stop_signal
                    )

                    active_thread = None
                    detection_thread = None
                    guidance_thread = None

                    sva_respond(
                        "System shutting down. Goodbye.",
                        priority=0
                    )

                    break

                # =================================================
                # MODE SELECTION
                # =================================================

                if awaiting_mode_selection:

                    # =================================================
                    # DETECTION MODE
                    # =================================================

                    if "detection" in text:

                        awaiting_mode_selection = False

                        kill_current_mode(
                            active_thread,
                            detection_thread,
                            guidance_thread,
                            stop_signal
                        )

                        active_thread = None
                        detection_thread = None
                        guidance_thread = None

                        sva_respond(
                            "Starting object detection.",
                            priority=2
                        )

                        stop_signal.clear()

                        detection_thread = threading.Thread(
                            target=run_detection,
                            args=(stop_signal, sva_respond),
                            daemon=True
                        )

                        detection_thread.start()

                        rec.Reset()

                    # =================================================
                    # READING MODE
                    # =================================================

                    elif "reading" in text:

                        awaiting_mode_selection = False

                        kill_current_mode(
                            active_thread,
                            detection_thread,
                            guidance_thread,
                            stop_signal
                        )

                        active_thread = None
                        detection_thread = None
                        guidance_thread = None

                        sva_respond(
                            "Starting reading mode.",
                            priority=2
                        )

                        stop_signal.clear()

                        active_thread = threading.Thread(
                            target=run_reading,
                            args=(stop_signal, sva_respond),
                            daemon=True
                        )

                        active_thread.start()

                        rec.Reset()

                    # =================================================
                    # ROUTE GUIDANCE MODE
                    # =================================================

                    elif "guidance" in text:

                        awaiting_mode_selection = False

                        kill_current_mode(
                            active_thread,
                            detection_thread,
                            guidance_thread,
                            stop_signal
                        )

                        active_thread = None
                        detection_thread = None
                        guidance_thread = None

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

                            # =====================================
                            # START DETECTION THREAD
                            # =====================================

                            stop_signal.clear()

                            detection_thread = threading.Thread(
                                target=run_detection,
                                args=(stop_signal, sva_respond),
                                daemon=True
                            )

                            detection_thread.start()

                            # =====================================
                            # START GUIDANCE THREAD
                            # =====================================

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

                        else:

                            awaiting_mode_selection = True

                            sva_respond(
                                "I could not hear your destination.",
                                priority=1
                            )

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
            stop_signal
        )

        try:

            stream.stop_stream()
            stream.close()

        except:
            pass

        p.terminate()

        speech_queue.put((0, None))

        print("System terminated.")