import asyncio
import websockets
import json
import pyttsx3
import threading
import queue
import socket
from zeroconf import Zeroconf, ServiceInfo


# =====================
# mDNS in background thread (NO asyncio conflict)
# =====================

def mdns_thread():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    zeroconf = Zeroconf()

    info = ServiceInfo(
        "_ws._tcp.local.",
        f"{hostname}._ws._tcp.local.",
        addresses=[socket.inet_aton(local_ip)],
        port=8765,
        server=f"{hostname}.local."
    )

    zeroconf.register_service(info)

    print("mDNS published")
    print("Use in Android:")
    print(f"ws://{hostname}.local:8765\n")

    # Keep thread alive
    try:
        while True:
            pass
    finally:
        zeroconf.unregister_service(info)
        zeroconf.close()


threading.Thread(target=mdns_thread, daemon=True).start()


# =====================
# TTS Worker
# =====================

speech_queue = queue.Queue()

def tts_worker():
    engine = pyttsx3.init()
    engine.setProperty("rate", 160)

    while True:
        text = speech_queue.get()
        if text is None:
            break
        try:
            print("🔊 Speaking:", text)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print("TTS Error:", e)
        finally:
            speech_queue.task_done()

threading.Thread(target=tts_worker, daemon=True).start()

def speak(text):
    speech_queue.put(text)


# =====================
# WebSocket Handler
# =====================

async def handler(ws):
    print("📱 Phone connected")

    last_instruction = ""
    last_distance = -1
    spoken_destination = ""

    try:
        async for message in ws:
            try:
                data = json.loads(message)
            except:
                continue

            if "lat" not in data:
                continue

            destination = data.get("destination", "")
            instruction = data.get("instruction", "")
            distance = int(float(data.get("remaining_distance", 0)))
            navigating = data.get("navigating", False)

            print("\n===== LIVE NAV DATA =====")
            print("Destination:", destination)
            print("Instruction:", instruction)
            print("Remaining Distance:", distance)
            print("Navigating:", navigating)
            print("=========================")

            # Speak destination once
            if destination and destination != spoken_destination:
                speak(f"Heading to {destination}")
                spoken_destination = destination

            # Speak instruction change
            if navigating and instruction and instruction != last_instruction:
                speak(instruction)
                last_instruction = instruction

            # Speak distance change
            if navigating and distance != last_distance:
                speak(f"{distance} meters remaining")
                last_distance = distance

    except websockets.exceptions.ConnectionClosed:
        print("❌ Phone disconnected")


# =====================
# Main Async Server
# =====================

async def main():
    print("WebSocket server running on port 8765\n")

    async with websockets.serve(handler, "0.0.0.0", 8765, ping_interval=None):
        await asyncio.Future()  # Run forever


# =====================
# Start
# =====================

if __name__ == "__main__":
    asyncio.run(main())
