import asyncio
import websockets
import json
import pyttsx3
import threading
import queue
import os
import subprocess
import time

# --- SPEECH SYSTEM ---
speech_queue = queue.Queue()

def tts_worker():
    engine = pyttsx3.init()
    engine.setProperty('rate', 155)
    engine.setProperty('volume', 0.9)

    while True:
        text = speech_queue.get()
        if text is None:
            break
        try:
            print(f"🔊 SPEAKING: {text}")
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"❌ TTS Error: {e}")
        finally:
            speech_queue.task_done()

threading.Thread(target=tts_worker, daemon=True).start()


async def handler(ws):
    print("\n✨ CONNECTION SUCCESS! Phone is now talking to Laptop.")

    # State tracking
    last_instr = None
    last_dist = None
    spoken_dest = None
    route_announced_for_dest = None

    last_nav_state = None
    last_stable_nav = None
    last_change_time = time.time()
    nav_initialized = False   # 🔥 FIX: prevents startup trigger

    message_count = 0
    last_instruction_time = 0

    try:
        async for message in ws:
            message_count += 1
            data = json.loads(message)

            # Extract data
            dest = data.get("destination", "")
            instr = data.get("instruction", "")
            dist = round(float(data.get("remaining_distance", 0)))
            nav = data.get("navigating", False)
            dest_reached = data.get("destination_reached", False)

            route_info = data.get("type") == "route_info"
            steps_count = data.get("steps_count", 0)
            total_distance = data.get("total_distance", 0)

            # Debug
            if message_count % 5 == 0:
                print(f"Nav: {nav} | Instr: {instr[:20]}... | Dist: {dist}m")

            # ===== TRACK NAV CHANGE =====
            if nav != last_nav_state:
                last_nav_state = nav
                last_change_time = time.time()

            # ===== STABILITY CHECK =====
            is_stable = (time.time() - last_change_time) >= 1.0

            # ===== NAVIGATION START/STOP (FIXED INITIALIZATION) =====
            if is_stable:

                # FIRST TIME ONLY INITIALIZATION (no speech)
                if not nav_initialized:
                    last_stable_nav = nav
                    nav_initialized = True
                    continue

                # REAL TRANSITIONS AFTER INIT
                if nav != last_stable_nav:

                    if nav is True:
                        if spoken_dest:
                            speech_queue.put("Navigation started")
                            print("🚗 NAVIGATION STARTED")
                            last_instr = None
                            last_dist = None

                    elif nav is False:
                        speech_queue.put("Navigation stopped")
                        print("🛑 NAVIGATION STOPPED")

                    last_stable_nav = nav

            # ===== DESTINATION DETECTED =====
            if dest and dest != spoken_dest and dest not in ["", "Not set"]:
                speech_queue.put(f"Destination is locked to {dest}")
                spoken_dest = dest
                route_announced_for_dest = None
                last_instr = None
                last_dist = None
                nav_initialized = False   # 🔥 reset on new destination
                print(f"🎯 NEW DESTINATION: {dest}")

            # ===== ROUTE LOADED =====
            if route_info and spoken_dest and route_announced_for_dest != spoken_dest:
                if total_distance < 1000:
                    dist_text = f"{int(total_distance)} meters"
                else:
                    dist_text = f"{total_distance/1000:.1f} kilometers"

                speech_queue.put(f"Route loaded. Total distance {dist_text}")
                route_announced_for_dest = spoken_dest
                print(f"🗺️ ROUTE: {steps_count} steps, {dist_text}")

            # ===== INSTRUCTIONS =====
            if nav and is_stable and not dest_reached and spoken_dest:
                current_time = time.time()

                if instr and instr != last_instr and instr != "Navigation not active":
                    if current_time - last_instruction_time > 2:
                        speech_queue.put(instr)
                        last_instr = instr
                        last_dist = None
                        last_instruction_time = current_time
                        print(f"🗣️ INSTRUCTION: {instr}")

                if dist > 5 and (last_dist is None or abs(dist - last_dist) >= 50):
                    if current_time - last_instruction_time > 1:
                        speech_queue.put(f"In {dist} meters")
                        last_dist = dist
                        last_instruction_time = current_time
                        print(f"📏 DISTANCE: {dist}m")

            # ===== DESTINATION REACHED =====
            if dest_reached:
                speech_queue.put("You have reached your destination")
                print("🎯 DESTINATION REACHED!")

                # RESET ALL
                spoken_dest = None
                route_announced_for_dest = None
                last_instr = None
                last_dist = None
                last_nav_state = None
                last_stable_nav = None
                nav_initialized = False
                last_change_time = time.time()

    except websockets.exceptions.ConnectionClosed as e:
        print(f"🔌 Connection Lost: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("👋 Phone disconnected")


async def main():
    try:
        adb_check = subprocess.run(["adb", "devices"], capture_output=True, text=True)

        if "device" not in adb_check.stdout:
            print("⚠️ No device found. Check USB debugging.")
        else:
            adb = os.path.join(os.environ['LOCALAPPDATA'], "Android", "Sdk", "platform-tools", "adb.exe")

            if os.path.exists(adb):
                result = subprocess.run(
                    [adb, "reverse", "tcp:8765", "tcp:8765"],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    print("✅ ADB Reverse: Port forwarded")
                else:
                    print(f"⚠️ ADB Reverse failed: {result.stderr}")
            else:
                print("⚠️ ADB not found")

    except Exception as e:
        print(f"⚠️ ADB setup error: {e}")

    print("\n🚀 Server running at ws://127.0.0.1:8765\n")

    async with websockets.serve(
        handler,
        "127.0.0.1",
        8765,
        ping_interval=20,
        ping_timeout=10
    ):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
