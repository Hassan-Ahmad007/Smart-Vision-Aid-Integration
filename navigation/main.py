from gps_input import GPSInput
from voice_input import get_destination
from navigation_api import geocode, get_route
from route_processor import process_route
from tracker import Tracker
from decision_engine import DecisionEngine
from voice_output import speak
import time

def main():
    gps = GPSInput()
    engine = DecisionEngine()

    destination = get_destination()
    if not destination:
        speak("Failed to get destination")
        return

    speak(f"Navigating to {destination}")

    start = gps.get_location()
    if not start:
        print("No GPS")
        return

    start = (start[0], start[1])
    end = geocode(destination)

    if not end:
        speak("Unable to get destination location")
        return
    route_data = get_route(start, end)
    steps, total_dist = process_route(route_data)

    if total_dist > 1000:
        speak(f"Distance {round(total_dist / 1000, 1)} kilometers")
    else:
        speak(f"Distance {int(total_dist)} meters")

    tracker = Tracker(steps)
    if steps:
        first_direction = steps[0]["direction"]
        speak(f"Start by going {first_direction}")

    while True:
        data = gps.get_location()
        if not data:
            continue

        lat, lon, obs, dist = data

        nav_cmd = tracker.update(lat, lon)
        cmd = engine.decide(obs, dist, nav_cmd)

        if cmd:
            speak(cmd)

        time.sleep(0.5)

if __name__ == "__main__":
    main()