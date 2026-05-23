# =========================
# navigation/route_guidance.py
# =========================

import firebase_admin
from firebase_admin import credentials, db

import time
import os

from navigation.gps_input import GPSInput
from navigation.navigation_api import geocode, get_route
from navigation.route_processor import process_route
from navigation.tracker import Tracker
from navigation.decision_engine import DecisionEngine


# =========================================================
# FIREBASE
# =========================================================

KEY_PATH = "serviceAccountKey.json"

try:

    if not firebase_admin._apps:

        if os.path.exists(KEY_PATH):

            cred = credentials.Certificate(KEY_PATH)

            firebase_admin.initialize_app(cred, {
                'databaseURL':
                    'https://guardianapp-3f979-default-rtdb.firebaseio.com/'
            })

            print("Firebase connected.")

        else:
            print("Firebase key not found.")

    ref = db.reference('blind_user_01')

except Exception as e:

    print(f"Firebase Error: {e}")


# =========================================================
# CLOUD UPDATE
# =========================================================

def update_cloud_status(lat, lng, status_msg="OK", error=False):

    try:

        if firebase_admin._apps:

            ref.update({
                'location': {
                    'lat': lat,
                    'lng': lng
                },
                'status': status_msg,
                'is_error': error,
                'last_heartbeat': time.time()
            })

    except:
        pass


# =========================================================
# MAIN GUIDANCE
# =========================================================

def run_guidance(stop_event, sva_respond, destination):
    def speak(text):

        try:

            if text and str(text).strip():
                print(f"[GUIDANCE SPEAK] {text}")

                sva_respond(str(text))

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

        return

    start_coords = (data[0], data[1])

    # -------------------------------------------------
    # GEOCODING
    # -------------------------------------------------

    speak(f"Finding route to {destination}")

    end = geocode(destination)

    if not end:

        speak("I could not find that destination.")

        return

    # -------------------------------------------------
    # ROUTE FETCH
    # -------------------------------------------------

    route_data = get_route(start_coords, end)

    steps, total_dist = process_route(route_data)

    if not steps:

        speak("Unable to calculate route.")

        return

    tracker = Tracker(steps)

    speak(
        f"Route found. Distance is "
        f"{int(total_dist)} meters."
    )

    # -------------------------------------------------
    # MAIN LOOP
    # -------------------------------------------------

    try:

        while not stop_event.is_set():

            data = gps.get_location()

            if not data:

                update_cloud_status(
                    0,
                    0,
                    "Waiting for GPS..."
                )

                time.sleep(1)

                continue

            lat, lon, obs, dist = data

            nav_cmd = tracker.update(lat, lon)

            cmd = engine.decide(
                obs,
                dist,
                nav_cmd
            )

            if cmd:
                speak(cmd)

            update_cloud_status(
                lat,
                lon,
                cmd if cmd else "Walking safely"
            )

            time.sleep(1)

    except Exception as e:

        print(f"GUIDANCE ERROR: {e}")

    finally:

        update_cloud_status(
            0,
            0,
            "Navigation stopped"
        )

        print("Guidance terminated.")