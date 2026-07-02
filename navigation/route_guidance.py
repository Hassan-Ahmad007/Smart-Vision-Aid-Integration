# =========================================
# navigation/route_guidance.py
# =========================================

import time
import os

from navigation.navigation_api import geocode, get_route
from navigation.route_processor import process_route
from navigation.tracker import Tracker


def run_guidance(stop_event, sva_respond, destination, update_cloud, gps):
    def speak(text, interrupt=False, priority=0):
        try:
            if text and str(text).strip():
                print(f"[GUIDANCE SPEAK] {text}")
                try:
                    sva_respond(str(text), priority=priority, interrupt=interrupt)
                except TypeError:
                    sva_respond(str(text), priority=priority)
        except Exception as e:
            print(f"SPEAK ERROR: {e}")

    print(f"\nSTARTING GUIDANCE TO: {destination}")

    # -------------------------------------------------
    # MANDATORY INITIAL SETUP
    # -------------------------------------------------

    speak(f"Finding route to {destination}")

    data = gps.get_location()
    if not data:
        speak("GPS not connected. Please move outdoors.")
        update_cloud(0, 0, status_msg="GPS Error", error=True, gps_on=False)
        return

    # Extract coordinates
    start_coords = (data[0], data[1])

    end = geocode(destination)
    if not end:
        speak("I could not find that destination.")
        update_cloud(start_coords[0], start_coords[1], status_msg="Geocoding Failed", error=True)
        return

    route_data = get_route(start_coords, end)
    steps, total_dist = process_route(route_data)
    if not steps:
        speak("Unable to calculate route.")
        update_cloud(start_coords[0], start_coords[1], status_msg="Route calculation failed", error=True)
        return

    tracker = Tracker(steps)

    speak(f"Route found. Distance is {int(total_dist)} meters.")
    time.sleep(0.5)

    if steps:
        first_dir = steps[0].get("direction", "STRAIGHT")
        first_distance = int(steps[0].get("distance", 0))
        speak(f"To start: Go {first_dir} for {first_distance} meters.")
        steps[0]["announced"] = True

    time.sleep(1.5)

    # Memory state to ensure we don't spam the same nav command
    last_nav_msg = ""

    # -------------------------------------------------
    # MAIN MONITORING LOOP (PURE NAVIGATION)
    # -------------------------------------------------

    try:
        while not stop_event.is_set():
            data = gps.get_location()

            if not data:
                update_cloud(0, 0, status_msg="GPS Signal Lost", error=True, gps_on=False)
                for _ in range(10):
                    if stop_event.is_set(): break
                    time.sleep(0.1)
                continue

            # We unpack 4 variables because gps_input.py safely returns 0, 0 for the last two
            lat, lon, _, _ = data

            # Get navigation directive from the Tracker based on coordinates
            nav_cmd = tracker.update(lat, lon)

            # Keep Firebase updated
            status_text = f"Navigating to {destination}"
            if nav_cmd:
                status_text += f" -> {nav_cmd}"

            update_cloud(lat=lat, lng=lon, status_msg=status_text, error=False, camera_on=True, gps_on=True)

            # ---------------------------------------------
            # SPEAK NAVIGATION
            # ---------------------------------------------
            if nav_cmd and nav_cmd != last_nav_msg:
                speak(nav_cmd, interrupt=False, priority=0)
                last_nav_msg = nav_cmd

            # Simple sleep to keep CPU usage low
            time.sleep(0.5)

    except Exception as e:
        print(f"GUIDANCE ERROR: {e}")
        update_cloud(0, 0, status_msg=f"Error: {str(e)}", error=True)
    finally:
        update_cloud(0, 0, status_msg="IDLE / Stopped", error=False, camera_on=False, gps_on=False)
        print("Route guidance fully stopped.")