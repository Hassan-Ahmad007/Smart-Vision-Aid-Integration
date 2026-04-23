def simplify(text):
    text = text.lower()
    if "left" in text:
        return "LEFT"
    elif "right" in text:
        return "RIGHT"
    else:
        return "STRAIGHT"


def process_route(data):
    try:
        steps_raw = data["steps"]
        total_dist = data["distance"]

        steps = []

        for step in steps_raw:
            instruction = step["maneuver"]["instruction"].lower()

            if "left" in instruction:
                direction = "LEFT"
            elif "right" in instruction:
                direction = "RIGHT"
            else:
                direction = "STRAIGHT"

            lat, lon = step["maneuver"]["location"][1], step["maneuver"]["location"][0]

            steps.append({
                "direction": direction,
                "lat": lat,
                "lon": lon
            })

        return steps, total_dist

    except Exception as e:
        print("PROCESS ROUTE ERROR:", e)
        return None, None