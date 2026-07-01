# =========================================
# navigation/route_guidance.py
# =========================================

import time
import os

from navigation.navigation_api import geocode, get_route
from navigation.route_processor import process_route
from navigation.tracker import Tracker
from navigation.decision_engine import DecisionEngine

# 🟢 Import the new decoupled structural handlers
from navigation.navigation_handler import NavigationHandler
from navigation.ultrasonic_handler import UltrasonicHandler


def run_guidance(stop_event, sva_respond, destination, update_cloud, gps):
    def speak(text, interrupt=False, priority=1):
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

    engine = DecisionEngine()
    nav_handler = NavigationHandler()
    sonar_handler = UltrasonicHandler()

    # -------------------------------------------------
    # MANDATORY INITIAL SETUP (The First 3 Commands)
    # -------------------------------------------------

    speak(f"Finding route to {destination}", interrupt=False, priority=0)

    data = gps.get_location()
    if not data:
        speak("GPS not connected. Please move outdoors.", priority=0)
        update_cloud(0, 0, status_msg="GPS Error", error=True, gps_on=False)
        return

    start_coords = (data[0], data[1])
    end = geocode(destination)
    if not end:
        speak("I could not find that destination.", priority=0)
        update_cloud(start_coords[0], start_coords[1], status_msg="Geocoding Failed", error=True)
        return

    route_data = get_route(start_coords, end)
    steps, total_dist = process_route(route_data)
    if not steps:
        speak("Unable to calculate route.", priority=0)
        update_cloud(start_coords[0], start_coords[1], status_msg="Route calculation failed", error=True)
        return

    tracker = Tracker(steps)

    speak(f"Route found. Distance is {int(total_dist)} meters.", interrupt=False, priority=0)
    time.sleep(0.2)

    if steps:
        first_dir = steps[0].get("direction", "STRAIGHT")
        first_distance = int(steps[0].get("distance", 0))
        speak(f"To start: Go {first_dir} for {first_distance} meters.", interrupt=False, priority=0)
        steps[0]["announced"] = True

    time.sleep(1.5)

    # -------------------------------------------------
    # MAIN MONITORING LOOP
    # -------------------------------------------------
    turn_state = 0  # 0 for Nav, 1 for Obstacle

    try:
        while not stop_event.is_set():
            data = gps.get_location()

            if not data:
                update_cloud(0, 0, status_msg="GPS Signal Lost", error=True, gps_on=False)
                for _ in range(10):
                    if stop_event.is_set(): break
                    time.sleep(0.1)
                continue

            lat, lon, obs, dist = data

            # Get directives from Tracking and Decision Frameworks
            nav_cmd = tracker.update(lat, lon)

            # Heartbeat Update
            status_text = f"Navigating to {destination}"
            update_cloud(lat=lat, lng=lon, status_msg=status_text, error=False, camera_on=True, gps_on=True)

            # =================================================
            # RUNTIME CO-PROCESSING (TURN-BASED)
            # =================================================

            # TURN 0: Navigation logic
            if turn_state == 0:
                # Check if path just cleared (passive check)
                _, _, cleared = sonar_handler.handle_ultrasonic(obs, dist)
                route_msg = nav_handler.handle_navigation(nav_cmd, cleared)

                if route_msg:
                    speak(route_msg, interrupt=cleared, priority=0)

                turn_state = 1  # Prepare for Obstacle Turn

            # TURN 1: Obstacle logic
            else:
                # Use force_check=True so it evaluates even if the timer hasn't hit 3s
                # NOTE: Ensure your ultrasonic_handler definition accepts 'force_check'
                obs_msg, is_urgent, _ = sonar_handler.handle_ultrasonic(obs, dist, force_check=True)

                if obs_msg:
                    speak(obs_msg, interrupt=is_urgent, priority=1)
                    nav_handler.reset_nav_memory()

                turn_state = 0  # Return to Navigation Turn

            # INTERRUPTIBLE SLEEP
            time.sleep(0.3)

    except Exception as e:
        print(f"GUIDANCE ERROR: {e}")
        update_cloud(0, 0, status_msg=f"Error: {str(e)}", error=True)
    finally:
        update_cloud(0, 0, status_msg="IDLE / Stopped", error=False, camera_on=False, gps_on=False)
        print("Route guidance fully stopped.")