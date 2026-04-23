from utils import distance
from config import STEP_THRESHOLD

class Tracker:
    def __init__(self, steps):
        self.steps = steps
        self.index = 0

    def update(self, lat, lon):
        if self.index >= len(self.steps):
            return "DESTINATION"

        step = self.steps[self.index]
        dist = distance(lat, lon, step["lat"], step["lon"])

        if dist < 30 and not step.get("announced"):
            step["announced"] = True
            return f"In 30 meters, go {step['direction']}"
        if dist < STEP_THRESHOLD:
            instr = step["instruction"]
            self.index += 1
            return instr
        print("Distance to step:", dist)

        return None