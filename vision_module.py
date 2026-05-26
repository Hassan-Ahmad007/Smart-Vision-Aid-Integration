import cv2
from ultralytics import YOLO
import time
from collections import deque



model = YOLO("yolov8n.pt")

# --- CONSTANTS ---

VOTE_THRESHOLD = 3
CONF_THRESH = 0.55
MAX_OBJECTS = 2
COOLDOWN_TIME = 7
TARGET_CLASSES = [0, 1, 2, 3, 5, 7, 9, 13, 15, 16, 17, 18, 19, 56, 57, 58, 59, 60, 61, 62, 63, 72]



def get_votes(cls, history):
    return sum(1 for f_set in history if cls in f_set)



def run_detection(stop_event, sva_respond, camera_index):
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    time.sleep(1)

    if not cap.isOpened():
        cap.release()

        sva_respond(
            "External camera is not available. Detection mode cannot start.",
            priority=0
        )

        return

    frame_count = 0
    skip_frames = 5
    detection_history = deque(maxlen=5)
    cooldowns = {}
    raw_detections = []

    print("Vision Module Started...")

    while not stop_event.is_set():
        ret, frame = cap.read()

        if not ret or frame is None:
            sva_respond(
                "Camera connection lost. Detection mode stopped.",
                priority=0
            )
            stop_event.set()
            break



        if frame_count % skip_frames == 0:
            results = model.predict(frame, conf=CONF_THRESH, classes=TARGET_CLASSES, verbose=False)[0]

            # Voting Logic
            current_frame_uniques = set(int(box.cls[0]) for box in results.boxes)
            detection_history.append(current_frame_uniques)

            possible_ids = set(cid for f_set in detection_history for cid in f_set)
            verified_ids = [cid for cid in possible_ids if get_votes(cid, detection_history) >= VOTE_THRESHOLD]

            # Top Detections
            top_boxes = sorted(results.boxes, key=lambda x: x.conf[0], reverse=True)[:MAX_OBJECTS]

            raw_detections = []
            current_time = time.time()

            for box in top_boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                name = model.names[cls]
                votes = get_votes(cls, detection_history)
                is_verified = cls in verified_ids

                # Speech Handling
                if is_verified:
                    last_spoken = cooldowns.get(cls, 0)
                    if current_time - last_spoken > COOLDOWN_TIME:
                        sva_respond(name + " ahead",priority=3)
                        cooldowns[cls] = current_time

                # Store visual data
                color = (0, 255, 0) if is_verified else (255, 100, 0)
                label = f"{'CONFIRMED' if is_verified else 'Analyzing'}: {name} {conf:.2f}"
                raw_detections.append({
                    "coords": box.xyxy[0].cpu().numpy().astype(int),
                    "label": label, "color": color
                })

        # Drawing
        for det in raw_detections:
            x1, y1, x2, y2 = det["coords"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), det["color"], 2)
            cv2.putText(frame, det["label"], (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, det["color"], 2)

        cv2.imshow("SVA - Detection Mode", frame)
        frame_count += 1
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()