import json
import time
import threading
import subprocess
import pyaudio
import cv2
import os

from queue import PriorityQueue
from vosk import Model, KaldiRecognizer

# =========================================================
# FIREBASE INTEGRATION (From Local)
# =========================================================
import firebase_admin
from firebase_admin import credentials, db

KEY_PATH = "serviceAccountKey.json"
db_ref = None

try:
    if not firebase_admin._apps:
        if os.path.exists(KEY_PATH):
            cred = credentials.Certificate(KEY_PATH)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://guardianapp-3f979-default-rtdb.firebaseio.com/'
            })
            print("Firebase connected successfully via main file.")
            db_ref = db.reference('blind_user_01')
        else:
            print("Firebase key not found in root path.")
except Exception as e:
    print(f"Firebase Initialization Error: {e}")


def update_cloud_status_central(lat, lng, status_msg="OK", error=False, camera_on=False, gps_on=False):
    try:
        if firebase_admin._apps and db_ref:
            db_ref.update({
                'location': {
                    'lat': lat,
                    'lng': lng
                },
                'status': status_msg,
                'is_error': error,
                'last_heartbeat': time.time(),
                'camera_active': camera_on,
                'gps_active': gps_on
            })
    except Exception as e:
        pass


# =========================================================
# MODULES (Combined GitHub + Local)
# =========================================================

from vision_module import run_detection
from reading_module import run_reading
from currency_module import run_currency
from navigation.voice_input import get_destination
from navigation.route_guidance import run_guidance
from navigation.gps_input import GPSInput  # Imported for central monitoring


# =========================================================
# CAMERA MANAGER
# =========================================================

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


# =========================================================
# SPEECH PRIORITY QUEUE
# =========================================================

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


# =========================================================
# STOP CURRENT MODE
# =========================================================

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


# =========================================================
# CLOUD BACKGROUND WORKER (Updated for Currency Mode)
# =========================================================

def cloud_monitor_worker(stop_signal, get_threads_func):
    """
    Monitors system state and pushes continuous telemetry to Firebase.
    """
    gps_instance = GPSInput()

    while not stop_signal.is_set():
        act_t, det_t, guid_t, curr_t = get_threads_func()

        # Check camera statuses based on running modules (Now includes Currency)
        camera_active = False
        if (det_t and det_t.is_alive()) or (act_t and act_t.is_alive()) or (curr_t and curr_t.is_alive()):
            camera_active = True

        # Check navigation status
        if guid_t and guid_t.is_alive():
            gps_data = gps_instance.get_location()
            if gps_data:
                lat, lon, obs, dist = gps_data
                update_cloud_status_central(
                    lat=lat,
                    lng=lon,
                    status_msg="Walking safely",
                    error=False,
                    camera_on=camera_active,
                    gps_on=True
                )
            else:
                update_cloud_status_central(
                    lat=0,
                    lng=0,
                    status_msg="Waiting for GPS...",
                    error=False,
                    camera_on=camera_active,
                    gps_on=False
                )
        else:
            # System idle or non-navigation modes
            status_msg = "System Active" if (act_t or det_t or curr_t) else "System Idle"
            update_cloud_status_central(
                lat=0,
                lng=0,
                status_msg=status_msg,
                error=False,
                camera_on=camera_active,
                gps_on=False
            )

        time.sleep(1.0)

    # When stopping execution
    update_cloud_status_central(0, 0, "Navigation stopped", error=False, camera_on=False, gps_on=False)


# =========================================================
# MAIN PROGRAM
# =========================================================

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


    # =====================================================
    # FIREBASE MONITORING INITIALIZATION
    # =====================================================
    
    # Lambda function to pass thread objects safely to the cloud worker
    def get_current_threads():
        return active_thread, detection_thread, guidance_thread, currency_thread

    # Start Central Cloud Monitor
    cloud_thread = threading.Thread(
        target=cloud_monitor_worker,
        args=(stop_signal, get_current_threads),
        daemon=True
    )
    cloud_thread.start()


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

                            # 🟢 FIREBASE SYNC: update_cloud_status_central passed here
                            guidance_thread = threading.Thread(
                                target=run_guidance,
                                args=(
                                    stop_signal,
                                    sva_respond,
                                    destination,
                                    update_cloud_status_central 
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