import vosk
import sys
import os
import json
import queue
import sounddevice as sd

# Load the model
if not os.path.exists("model"):
    print(
        "Please download the model from https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.")
    sys.exit(1)

model = vosk.Model("model")
audio_queue = queue.Queue()


def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(bytes(indata))


def listen_for_command():
    """Listens to the microphone and returns recognized text."""
    # Standard settings for Vosk
    device_info = sd.query_devices(None, 'input')
    samplerate = int(device_info['default_samplerate'])

    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        rec = vosk.KaldiRecognizer(model, samplerate)
        print("Vosk is listening...")

        while True:
            data = audio_queue.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                command = result.get("text", "").lower()
                if command:
                    return command