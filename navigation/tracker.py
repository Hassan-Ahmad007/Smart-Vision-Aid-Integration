from utils import distance
from config import STEP_THRESHOLD

class Tracker:
    def __init__(self, steps):
        self.steps = steps
        self.index = 0
        self.last_pos = None

    def update(self, lat, lon):

        # ---------------- ARRIVAL ----------------
        if self.index >= len(self.steps):
            return "ARRIVED"

        # ---------------- IGNORE GPS NOISE ----------------
        if self.last_pos:
            prev_lat, prev_lon = self.last_pos
            movement = distance(prev_lat, prev_lon, lat, lon)

            # ignore tiny movement (<5m)
            if movement < 5:
                return None

        self.last_pos = (lat, lon)

        step = self.steps[self.index]

        step_lat = step["lat"]
        step_lon = step["lon"]

        dist = distance(lat, lon, step_lat, step_lon)

        print("Distance to step:", dist)

        # ---------------- IGNORE HUGE GPS JUMPS ----------------
        if dist > 200:
            return None

        # ---------------- LOOKAHEAD ----------------
        if dist < 40 and not step.get("announced"):
            step["announced"] = True
            return f"In 40 meters, go {step['direction']}"

        # ---------------- MAIN STEP TRIGGER ----------------
        if dist < STEP_THRESHOLD:
            direction = step["direction"]
            self.index += 1
            return f"Go {direction}"

        return None