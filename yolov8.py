import cv2
from ultralytics import YOLO
import pyttsx3
import threading
import queue
import time
from collections import deque


# -----------------------------
# 1. FASTER TTS WORKER
# -----------------------------
def tts_worker(q):
    engine = pyttsx3.init()
    engine.setProperty('rate', 160)

    while True:
        text = q.get()
        if text is None: break

        # Anti-Lag: If the queue is backed up, clear it and speak only the newest item
        if q.qsize() > 1:
            with q.mutex:
                q.queue.clear()

        engine.say(text + " ahead")
        engine.runAndWait()
        q.task_done()


tts_queue = queue.Queue()
threading.Thread(target=tts_worker, args=(tts_queue,), daemon=True).start()

# -----------------------------
# 2. FASTER MODEL & SETTINGS
# -----------------------------
# SWITCHED TO NANO (yolov8n.pt) for 3x Speed Boost
model = YOLO("yolov8s.pt")
cap = cv2.VideoCapture(2)

frame_count = 0
skip_frames = 5
active_boxes = []
cooldowns = {}

# MEMORY SETTINGS
detection_history = deque(maxlen=5)
VOTE_THRESHOLD = 3  # Needs 3 votes to confirm
CONF_THRESH = 0.55  # Increased slightly to reduce false positives
MAX_OBJECTS = 2
TARGET_CLASSES = [0, 1, 2, 3, 5, 7, 9, 13, 15, 16, 17, 18, 19, 56, 57, 58, 59, 60, 61, 62, 63, 72]

# -----------------------------
# 3. MAIN LOOP
# -----------------------------
while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    # AI PROCESS (Every 5th frame)
    if frame_count % skip_frames == 0:
        results = model.predict(frame, conf=CONF_THRESH, classes=TARGET_CLASSES, verbose=False)[0]

        # A. RECORD RAW DETECTIONS
        # (This is what the AI sees RIGHT NOW, even if it's a glitch)
        current_frame_uniques = set([int(box.cls[0]) for box in results.boxes])
        detection_history.append(current_frame_uniques)

        # B. CALCULATE VOTES
        verified_ids = []
        possible_ids = set(cid for frame_set in detection_history for cid in frame_set)

        # Debug string to show you the "hidden" thinking
        debug_log = []

        for cid in possible_ids:
            # Count votes strictly
            votes = sum(1 for frame_set in detection_history if cid in frame_set)

            # Show the user what the AI is thinking (e.g., "Bed: 2/3")
            name = model.names[cid]
            if votes > 0:
                debug_log.append(f"{name}: {votes}/{VOTE_THRESHOLD}")

            # Only verify if it meets the threshold
            if votes >= VOTE_THRESHOLD:
                verified_ids.append(cid)

        # Print the "Brain State" so you can see votes accumulating
        if debug_log:
            print(f"Frame {frame_count} Stats: " + " | ".join(debug_log))
        else:
            print(f"Frame {frame_count}: Clean")

        # C. FILTER & SPEAK
        active_boxes = []
        current_time = time.time()

        # We sort by confidence so we prioritize the best detections
        sorted_boxes = sorted(results.boxes, key=lambda x: x.conf[0], reverse=True)

        for box in sorted_boxes:
            cls = int(box.cls[0])

            # Only Show/Speak if VERIFIED
            if cls in verified_ids:
                if len(active_boxes) < MAX_OBJECTS:
                    active_boxes.append(box)
                    name = model.names[cls]

                    # Cooldown Logic
                    last_spoken = cooldowns.get(cls, 0)
                    if (current_time - last_spoken > 5):
                        tts_queue.put(name)
                        cooldowns[cls] = current_time

    # -----------------------------
    # 4. DRAWING
    # -----------------------------
    for box in active_boxes:
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
        cls = int(box.cls[0])
        # We add "CONFIRMED" to the label so you know it passed the test
        label = f"CONFIRMED: {model.names[cls]}"
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imshow("Vision Assistant (Fast Mode)", frame)
    frame_count += 1
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()
tts_queue.put(None)