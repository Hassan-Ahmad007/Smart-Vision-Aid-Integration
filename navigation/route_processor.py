def simplify(text):
    text = text.lower()

    if "left" in text:
        return "LEFT"
    elif "right" in text:
        return "RIGHT"
    elif "u-turn" in text:
        return "UTURN"
    else:
        return "STRAIGHT"


def process_route(data):
    try:
        # ---------------- VALIDATE DATA ----------------
        if not data or "steps" not in data:
            print("PROCESS ROUTE ERROR: Invalid route data")
            return None, None

        steps_raw = data["steps"]
        total_dist = data.get("distance", 0)

        steps = []

        for step in steps_raw:
            maneuver = step.get("maneuver", {})

            # ---------------- EXTRACT INSTRUCTION ----------------
            instruction_text = maneuver.get("instruction", "")
            direction = simplify(instruction_text)

            # ---------------- EXTRACT LOCATION ----------------
            location = maneuver.get("location", None)

            if not location or len(location) != 2:
                continue  # skip invalid step

            lon, lat = location

            # ---------------- STEP DISTANCE ----------------
            step_distance = step.get("distance", 0)

            # ---------------- BUILD STEP ----------------
            steps.append({
                "direction": direction,              # LEFT / RIGHT / STRAIGHT
                "instruction": instruction_text,     # full human-readable text
                "lat": lat,
                "lon": lon,
                "distance": step_distance,           # meters
                "announced": False                   # for lookahead control
            })

        # ---------------- FINAL VALIDATION ----------------
        if not steps:
            print("PROCESS ROUTE ERROR: No valid steps parsed")
            return None, None

        return steps, total_dist

    except Exception as e:
        print("PROCESS ROUTE ERROR:", e)
        return None, None