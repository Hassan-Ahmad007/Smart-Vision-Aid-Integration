# =======================================
# navigation/ultrasonic_handler.py
# =======================================
import time


class UltrasonicHandler:
    def __init__(self):
        self.last_spoken_dist = -1
        self.obstacle_active = False
        self.last_speak_time = 0

    def handle_ultrasonic(self, obs, dist, threshold=150, critical_dist=30, force_check=False):
        """
        Returns: (message, interrupt_flag, cleared_flag)
        If force_check is True, it evaluates the obstacle status regardless of the 3s timer.
        """
        current_time = time.time()

        # 1. PATH IS PHYSICALLY CLEAR
        if obs == 0 or dist > threshold:
            if self.obstacle_active:
                self.obstacle_active = False
                self.last_spoken_dist = -1
                return None, False, True  # Path just cleared
            return None, False, False

        # 2. OBSTACLE DETECTED
        self.obstacle_active = True
        msg = f"Stop. Obstacle at {int(dist)} centimeters." if dist <= critical_dist else f"Obstacle at {int(dist)} centimeters."

        # 3. SPEAK LOGIC
        time_passed = (current_time - self.last_speak_time) >= 3.0
        is_closer = (self.last_spoken_dist != -1 and dist < (self.last_spoken_dist - 4))

        # If it's a new obstacle, 3 seconds passed, got closer, OR we are forcing a check
        if force_check or self.last_spoken_dist == -1 or time_passed or is_closer:
            self.last_spoken_dist = dist
            self.last_speak_time = current_time
            # Return message only if it's the right time to speak
            return msg, is_closer, False

        # If we are here, there is an obstacle, but we aren't "due" to speak yet.
        return None, False, False

    def reset_obstacle_memory(self):
        self.last_spoken_dist = -1