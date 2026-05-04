import firebase_admin
from firebase_admin import credentials, db
import time
from gps_input import GPSInput
from voice_input import get_destination
from navigation_api import geocode, get_route
from route_processor import process_route
from tracker import Tracker
from decision_engine import DecisionEngine
from voice_output import speak

# --- FIREBASE INITIALIZATION ---
# Using your specific URL and the renamed serviceAccountKey.json
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://guardianapp-3f979-default-rtdb.firebaseio.com/'
    })
    # Reference to the guardian's view of the blind user
    ref = db.reference('blind_user_01')
    print("Firebase initialized successfully.")
except Exception as e:
    print(f"Failed to initialize Firebase: {e}")


def update_cloud_status(lat, lng, status_msg="System OK", error=False):
    """Sends current GPS and system health to the Guardian App via Firebase."""
    try:
        ref.update({
            'location': {'lat': lat, 'lng': lng},
            'status': status_msg,
            'is_error': error,
            'last_heartbeat': time.time()  # Crucial for Crash Detection
        })
    except Exception as e:
        print(f"Cloud Sync Failed: {e}")


def main():
    gps = GPSInput()
    engine = DecisionEngine()

    destination = get_destination()
    if not destination:
        speak("Failed to get destination")
        update_cloud_status(0, 0, "Failed to get destination", error=True)
        return

    speak(f"Navigating to {destination}")

    start = gps.get_location()
    if not start:
        print("No GPS")
        update_cloud_status(0, 0, "No GPS Connection", error=True)
        return

    # Extract lat/lon for geocoding/routing
    start_coords = (start[0], start[1])
    end = geocode(destination)

    if not end:
        speak("Unable to get destination location")
        update_cloud_status(start[0], start[1], "Destination Unreachable", error=True)
        return

    route_data = get_route(start_coords, end)
    steps, total_dist = process_route(route_data)

    if total_dist > 1000:
        speak(f"Distance {round(total_dist / 1000, 1)} kilometers")
    else:
        speak(f"Distance {int(total_dist)} meters")

    tracker = Tracker(steps)
    if steps:
        first_direction = steps[0]["direction"]
        speak(f"Start by going {first_direction}")

    print("System started. Syncing with Guardian App...")

    # --- MAIN LOOP ---
    try:
        while True:
            data = gps.get_location()
            if not data:
                # Still heartbeat even if GPS is temporarily lost
                update_cloud_status(0, 0, "Waiting for GPS Fix...", error=False)
                continue

            lat, lon, obs, dist = data

            # Get command from Decision Engine
            nav_cmd = tracker.update(lat, lon)
            cmd = engine.decide(obs, dist, nav_cmd)

            if cmd:
                speak(cmd)

            # --- SYNC TO GUARDIAN ---
            # We use the decision engine's output as the 'status_msg' for the guardian
            current_status = cmd if cmd else "User walking safely"
            update_cloud_status(lat, lon, current_status)

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("Shutting down...")
        update_cloud_status(0, 0, "User Logged Off", error=True)
    except Exception as e:
        print(f"Critical System Failure: {e}")
        # Notify the guardian of the specific crash reason
        update_cloud_status(0, 0, f"CRASH: {str(e)}", error=True)


if __name__ == "__main__":
    main()
