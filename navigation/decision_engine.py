import time
from config import CRITICAL_OBS, OBS_THRESHOLD, COOLDOWN

class DecisionEngine:
    def __init__(self):
        self.last_cmd = None
        self.last_time = 0

    def decide(self, obs, dist, nav_cmd):
        now = time.time()

        if obs == 1 and dist < CRITICAL_OBS:
            cmd = "STOP"
        elif obs == 1 and dist < OBS_THRESHOLD:
            cmd = "OBSTACLE"
        elif nav_cmd:
            cmd = nav_cmd
        else:
            return None

        if cmd == self.last_cmd and (now - self.last_time < COOLDOWN):
            return None

        self.last_cmd = cmd
        self.last_time = now
        return cmd