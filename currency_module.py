import cv2
import time
import re
from collections import deque
from ultralytics import YOLO

currency_model = YOLO("best.pt")

print("Currency model classes:", currency_model.names)

# =========================================================
# SETTINGS FOR LOGITECH C270 720P WEBCAM
# =========================================================

CONF_THRESH = 0.55
IOU_THRESH = 0.50
SKIP_FRAMES = 3

STABLE_FRAMES = 4
MIN_BOX_AREA_RATIO = 0.01

GUIDE_COOLDOWN = 10
SPEAK_COOLDOWN = 3

NO_NOTE_RESET_FRAMES = 8

NOTE_VALUES = [10, 20, 50, 75, 100, 500, 1000, 5000]


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def extract_amount(label):
    label = str(label).lower()
    numbers = re.findall(r"\d+", label)

    if not numbers:
        return None

    value = int(numbers[0])

    if value in NOTE_VALUES:
        return value

    return None


def calculate_iou(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    x1 = max(ax1, bx1)
    y1 = max(ay1, by1)
    x2 = min(ax2, bx2)
    y2 = min(ay2, by2)

    inter_w = max(0, x2 - x1)
    inter_h = max(0, y2 - y1)
    inter_area = inter_w * inter_h

    area_a = max(1, (ax2 - ax1) * (ay2 - ay1))
    area_b = max(1, (bx2 - bx1) * (by2 - by1))

    return inter_area / float(area_a + area_b - inter_area)


def remove_duplicate_boxes(detections):
    detections = sorted(detections, key=lambda d: d["conf"], reverse=True)
    final = []

    for det in detections:
        duplicate = False

        for kept in final:
            overlap = calculate_iou(det["coords"], kept["coords"])

            if overlap > IOU_THRESH:
                duplicate = True
                break

        if not duplicate:
            final.append(det)

    return final


# def make_regions(frame):
#     """
#     720p C270 webcam:
#     Full frame + center/left/right crops.
#     Helps detect a note even when glasses camera is slightly misaligned.
#     """
#
#     h, w = frame.shape[:2]
#     mid_x = w // 2
#     overlap = int(w * 0.12)
#
#     regions = []
#
#     regions.append(("full", frame, 0, 0))
#
#     regions.append(
#         ("left", frame[:, 0:mid_x + overlap], 0, 0)
#     )
#
#     regions.append(
#         ("right", frame[:, mid_x - overlap:w], mid_x - overlap, 0)
#     )
#
#     return regions

def make_regions(frame):
    return [("full", frame, 0, 0)]

def detect_notes(frame):
    frame_h, frame_w = frame.shape[:2]
    frame_area = frame_w * frame_h

    all_detections = []

    for region_name, img, offset_x, offset_y in make_regions(frame):

        results = currency_model.predict(
            img,
            conf=CONF_THRESH,
            imgsz=640,
            iou=IOU_THRESH,
            max_det=10,
            verbose=False
        )[0]

        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            label = currency_model.names[cls_id]

            amount = extract_amount(label)

            if amount is None:
                continue

            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

            x1 += offset_x
            x2 += offset_x
            y1 += offset_y
            y2 += offset_y

            x1 = max(0, min(frame_w - 1, x1))
            x2 = max(0, min(frame_w - 1, x2))
            y1 = max(0, min(frame_h - 1, y1))
            y2 = max(0, min(frame_h - 1, y2))

            box_area = max(1, (x2 - x1) * (y2 - y1))
            box_area_ratio = box_area / frame_area

            if box_area_ratio < MIN_BOX_AREA_RATIO:
                continue

            all_detections.append({
                "coords": (x1, y1, x2, y2),
                "amount": amount,
                "label": label,
                "conf": conf
            })

    return remove_duplicate_boxes(all_detections)


def get_best_note(detections):
    if not detections:
        return None

    return sorted(
        detections,
        key=lambda d: d["conf"],
        reverse=True
    )[0]


def guide_user(note, frame_w, frame_h):
    """
    Optimized for Logitech C270 720p webcam mounted on glasses.
    User should bring the note into the center field of view.
    """

    if note is None:
        return "Bring the note in front of your face."

    x1, y1, x2, y2 = note["coords"]

    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2

    box_w = x2 - x1
    box_h = y2 - y1

    area_ratio = (box_w * box_h) / (frame_w * frame_h)

    center_left = frame_w * 0.35
    center_right = frame_w * 0.65
    center_top = frame_h * 0.30
    center_bottom = frame_h * 0.70

    if cx < center_left:
        return "Move the note slightly right."
    elif cx > center_right:
        return "Move the note slightly left."
    elif cy < center_top:
        return "Move the note slightly down."
    elif cy > center_bottom:
        return "Move the note slightly up."
    elif area_ratio < 0.05:
        return "Bring the note closer."
    elif area_ratio > 0.55:
        return "Move the note slightly away."
    else:
        return "Hold steady."


# =========================================================
# MAIN CURRENCY MODE
# =========================================================

def run_currency(stop_event, sva_respond, camera_index):
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

    cap.set(
        cv2.CAP_PROP_FOURCC,
        cv2.VideoWriter_fourcc(*'MJPG')
    )

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    time.sleep(2)


    ret, test_frame = cap.read()


    if not cap.isOpened():
        cap.release()
        sva_respond("Camera is not available. Currency mode cannot start.", priority=0)
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    sva_respond(
        "Currency counting mode active. Show one note at a time.",
        priority=2
    )

    frame_count = 0
    display_detections = []

    stable_history = deque(maxlen=STABLE_FRAMES)

    total_amount = 0
    total_notes = 0

    waiting_for_note_remove = False
    no_note_frames = 0

    last_guide_time = 0
    last_speak_time = 0

    try:
        while not stop_event.is_set():

            ret, frame = cap.read()

            if not ret or frame is None:
                if not stop_event.is_set():
                    sva_respond(
                        "Camera connection lost. Currency mode stopped.",
                        priority=0
                    )
                break

            frame_h, frame_w = frame.shape[:2]

            # Draw center target box for glasses camera
            center_left = int(frame_w * 0.35)
            center_right = int(frame_w * 0.65)
            center_top = int(frame_h * 0.30)
            center_bottom = int(frame_h * 0.70)

            cv2.rectangle(
                frame,
                (center_left, center_top),
                (center_right, center_bottom),
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                "Place note inside center box",
                (center_left, center_top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                "Currency Counting Mode",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            if frame_count % SKIP_FRAMES == 0:

                display_detections = detect_notes(frame)
                best_note = get_best_note(display_detections)

                now = time.time()

                if waiting_for_note_remove:

                    if best_note is None:
                        no_note_frames += 1
                    else:
                        no_note_frames = 0

                    if no_note_frames >= NO_NOTE_RESET_FRAMES:
                        waiting_for_note_remove = False
                        stable_history.clear()
                        no_note_frames = 0

                        if not stop_event.is_set():
                            sva_respond(
                                "Ready for next note.",
                                priority=2
                            )

                else:

                    if best_note is None:
                        stable_history.clear()

                        if now - last_guide_time > GUIDE_COOLDOWN:
                            sva_respond(
                                "Bring the note in front of your face.",
                                priority=3
                            )
                            last_guide_time = now

                    else:
                        amount = best_note["amount"]
                        confidence = best_note["conf"]

                        stable_history.append(amount)

                        if now - last_guide_time > GUIDE_COOLDOWN:
                            guide = guide_user(best_note, frame_w, frame_h)

                            if guide != "Hold steady.":
                                sva_respond(guide, priority=3)

                            last_guide_time = now

                        if (
                            len(stable_history) == STABLE_FRAMES
                            and all(a == amount for a in stable_history)
                            and confidence >= CONF_THRESH
                            and now - last_speak_time > SPEAK_COOLDOWN
                        ):
                            total_amount += amount
                            total_notes += 1

                            sva_respond(
                                f"{amount} rupees added. "
                                f"Total is {total_amount} rupees. "
                                f"Remove this note and show next note.",
                                priority=2
                            )

                            waiting_for_note_remove = True
                            stable_history.clear()
                            last_speak_time = now

            for det in display_detections:
                x1, y1, x2, y2 = det["coords"]
                amount = det["amount"]
                conf = det["conf"]

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    f"{amount} Rs {conf * 100:.1f}%",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

            cv2.putText(
                frame,
                f"Total: {total_amount} Rs | Notes: {total_notes}",
                (20, frame_h - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.imshow("SVA - Currency Counting Mode", frame)

            frame_count += 1

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                stop_event.set()
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print(currency_model.model.yaml)
        sva_respond(
            f"Currency mode stopped. Final total is {total_amount} rupees. Goodbye.",
            priority=2
        )