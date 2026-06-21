# =========================
# navigation/route_guidance.py
# =========================

import time
import os

from navigation.gps_input import GPSInput
from navigation.navigation_api import geocode, get_route
from navigation.route_processor import process_route
from navigation.tracker import Tracker
from navigation.decision_engine import DecisionEngine

# =========================================================
# MAIN GUIDANCE
# =========================================================

def run_guidance(stop_event, sva_respond, destination, update_cloud):
    def speak(text):
        try:
            if text and str(text).strip():
                print(f"[GUIDANCE SPEAK] {text}")
                sva_respond(str(text), priority=1)
        except Exception as e:
            print(f"SPEAK ERROR: {e}")

    print(f"\nSTARTING GUIDANCE TO: {destination}")

    gps = GPSInput()
    engine = DecisionEngine()

    # -------------------------------------------------
    # INITIAL GPS
    # -------------------------------------------------
    data = gps.get_location()
    if not data:
        speak("GPS not connected. Please move outdoors.")
        # Call the passed update function
        update_cloud(0, 0, status_msg="GPS Error", error=True, gps_on=False)
        return

    start_coords = (data[0], data[1])

    # -------------------------------------------------
    # GEOCODING
    # -------------------------------------------------
    speak(f"Finding route to {destination}")
    end = geocode(destination)
    if not end:
        speak("I could not find that destination.")
        update_cloud(start_coords[0], start_coords[1], status_msg="Geocoding Failed", error=True)
        return

    # -------------------------------------------------
    # ROUTE FETCH
    # -------------------------------------------------
    route_data = get_route(start_coords, end)
    steps, total_dist = process_route(route_data)
    if not steps:
        speak("Unable to calculate route.")
        update_cloud(start_coords[0], start_coords[1], status_msg="Route calculation failed", error=True)
        return

    tracker = Tracker(steps)
    speak(f"Route found. Distance is {int(total_dist)} meters.")

    # 👇 FIXED IMMEDIATE INSTRUCTION LOGIC 👇
    if steps:
        # Use the simplified direction (STRAIGHT/LEFT/RIGHT) instead of raw map text
        first_dir = steps[0].get("direction", "STRAIGHT")
        first_distance = int(steps[0].get("distance", 0))
        
        # Instantly announce the first step and its distance cleanly
        speak(f"To start: Go {first_dir} for {first_distance} meters.")
        
        # Mark as announced so the tracker doesn't repeat it right away
        steps[0]["announced"] = True
    # 👆 ================================== 👆

    # -------------------------------------------------
    # MAIN LOOP
    # -------------------------------------------------
    try:
        while not stop_event.is_set():
            if stop_event.is_set():
                break

            data = gps.get_location()

            # =========================================
            # GPS FAILED
            # =========================================
            if not data:
                update_cloud(0, 0, status_msg="GPS Signal Lost", error=True, gps_on=False)
                for _ in range(10):
                    if stop_event.is_set():
                        break
                    time.sleep(0.1)
                continue

            if stop_event.is_set():
                break

            lat, lon, obs, dist = data

            # =========================================
            # TRACKER
            # =========================================
            nav_cmd = tracker.update(lat, lon)
            if nav_cmd:
                print(f"[NAV ROUTE STATUS] Directive: {nav_cmd}")

            # =========================================
            # DECISION ENGINE
            # =========================================
            cmd = engine.decide(obs, dist, nav_cmd)

            # =========================================
            # KEEP FIREBASE ONLINE (Heartbeat Update)
            # =========================================
            status_text = f"Navigating to {destination} -> {cmd if cmd else 'Moving Straight'}"
            update_cloud(
                lat=lat,
                lng=lon,
                status_msg=status_text,
                error=False,
                camera_on=True,
                gps_on=True
            )

            # =========================================
            # SPEAK
            # =========================================
            if cmd:
                speak(cmd)

            # INTERRUPTIBLE SLEEP
            for _ in range(10):
                if stop_event.is_set():
                    break
                time.sleep(0.1)

    except Exception as e:
        print(f"GUIDANCE ERROR: {e}")
        update_cloud(0, 0, status_msg=f"Error: {str(e)}", error=True)
    finally:
        update_cloud(0, 0, status_msg="IDLE / Stopped", error=False, camera_on=False, gps_on=False)
        print("Guidance terminated.")
        print("Route guidance fully stopped.")