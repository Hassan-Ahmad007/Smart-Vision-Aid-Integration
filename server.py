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
    print(f"\n✨ CONNECTION SUCCESS! Phone is now talking to Laptop.")
    
    # State tracking
    last_instr = None
    last_dist = None
    spoken_dest = None
    route_announced_for_dest = None
    navigation_started_for_dest = None
    last_nav_state = False
    message_count = 0
    stable_nav_count = 0  # Counter for stable navigation detection
    last_instruction_time = 0
    
    try:
        async for message in ws:
            message_count += 1
            data = json.loads(message)
            
            # Print first few messages
            if message_count <= 3:
                print(f"Working")

            # Extract ALL data from phone
            dest = data.get("destination", "")
            instr = data.get("instruction", "")
            dist = round(float(data.get("remaining_distance", 0)))
            nav = data.get("navigating", False)
            dest_reached = data.get("destination_reached", False)
            
            # Get route info
            route_info = data.get("type") == "route_info"
            steps_count = data.get("steps_count", 0)
            total_distance = data.get("total_distance", 0)
            
            # Print debug info occasionally
            if message_count % 5 == 0:
                lat = data.get("lat", 0)
                lon = data.get("lon", 0)
                print(f" GPS:  Nav: {nav} | Instr: {instr[:20]}... | Dist: {dist}m")

            # ===== STABLE NAVIGATION DETECTION =====
            # We need 3 consecutive True or False to consider it stable
            if nav == last_nav_state:
                stable_nav_count += 1
            else:
                stable_nav_count = 0
            
            # ===== DETECT NAVIGATION START (only when stable) =====
            if stable_nav_count >= 3 and nav and not last_nav_state and spoken_dest:
                # Navigation just started (stable)
                if navigation_started_for_dest != spoken_dest or navigation_started_for_dest is None:
                    speech_queue.put("Navigation started")
                    navigation_started_for_dest = spoken_dest
                    print("🚗 NAVIGATION STARTED (stable)")
                    # Reset instruction tracking for new navigation session
                    last_instr = None
                    last_dist = None
            
            # ===== DETECT NAVIGATION STOP (only when stable) =====
            if stable_nav_count >= 3 and not nav and last_nav_state:
                # Navigation just stopped (stable)
                print("🛑 Navigation stopped (stable)")
                # Don't speak anything, just reset for next start
                navigation_started_for_dest = None  # Allow "Navigation started" again
            
            last_nav_state = nav

            # ===== DESTINATION ANNOUNCEMENT =====
            if dest and dest != spoken_dest and dest not in ["", "Not set"]:
                # New destination detected
                speech_queue.put(f"Destination is locked to {dest}")
                spoken_dest = dest
                route_announced_for_dest = None
                navigation_started_for_dest = None
                last_instr = None
                last_dist = None
                print(f"🎯 NEW DESTINATION: {dest}")

            # ===== ROUTE LOADED ANNOUNCEMENT =====
            if route_info and spoken_dest and route_announced_for_dest != spoken_dest:
                # Format distance nicely
                if total_distance < 1000:
                    dist_text = f"{int(total_distance)} meters"
                else:
                    dist_text = f"{total_distance/1000:.1f} kilometers"
                
                speech_queue.put(f"Route loaded. Total distance {dist_text}")
                route_announced_for_dest = spoken_dest
                print(f"🗺️ NEW ROUTE: {steps_count} steps, {dist_text}")

            # ===== NAVIGATION INSTRUCTIONS (only when STABLY navigating) =====
            if nav and stable_nav_count >= 3 and not dest_reached and spoken_dest:
                current_time = time.time()
                
                # Speak instruction when it changes (with debounce)
                if instr and instr != last_instr and instr != "Navigation not active":
                    # Don't speak too frequently
                    if current_time - last_instruction_time > 2:  # At least 2 seconds between instructions
                        speech_queue.put(instr)
                        last_instr = instr
                        last_dist = None
                        last_instruction_time = current_time
                        print(f"🗣️ INSTRUCTION: {instr}")

                # Speak distance updates (every 50 meters)
                if dist > 5 and (last_dist is None or abs(dist - last_dist) >= 50):
                    if current_time - last_instruction_time > 1:  # At least 1 second between distance updates
                        speech_queue.put(f"In {dist} meters")
                        last_dist = dist
                        last_instruction_time = current_time
                        print(f"📏 DISTANCE: {dist}m")

            # ===== DESTINATION REACHED =====
            if dest_reached:
                speech_queue.put("You have reached your destination")
                print("🎯 DESTINATION REACHED!")
                # Reset all states
                spoken_dest = None
                route_announced_for_dest = None
                navigation_started_for_dest = None
                last_instr = None
                last_dist = None
                last_nav_state = False
                stable_nav_count = 0

    except websockets.exceptions.ConnectionClosed as e:
        print(f"🔌 Connection Lost: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("👋 Phone disconnected")

async def main():
    # Force the reverse tunnel every time the script starts
    try:
        # First check if any device is connected
        adb_check = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        if "device" not in adb_check.stdout:
            print("⚠️ No device found. Please check:")
            print("   1. USB debugging is enabled")
            print("   2. Phone is connected via USB")
            print("   3. 'Allow USB debugging' prompt was accepted")
        else:
            # Setup reverse tunnel
            adb = os.path.join(os.environ['LOCALAPPDATA'], "Android", "Sdk", "platform-tools", "adb.exe")
            if os.path.exists(adb):
                result = subprocess.run([adb, "reverse", "tcp:8765", "tcp:8765"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ ADB Reverse: Port 8765 forwarded successfully")
                else:
                    print(f"⚠️ ADB Reverse failed: {result.stderr}")
            else:
                print("⚠️ ADB not found at:", adb)
    except Exception as e:
        print(f"⚠️ ADB setup error: {e}")
    
    print("\n" + "="*50)
    print("🚀 Server listening on ws://127.0.0.1:8765")
    print("📱 Waiting for phone connection...")
    print("="*50 + "\n")
    
    # Start server with ping enabled
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
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")