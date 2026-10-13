from picamera2 import Picamera2
from gpiozero import LED
import cv2
import time
import signal
import sys
from pathlib import Path

from ultralytics import YOLO

# ----------------------------
# LED GPIO pins
# ----------------------------
GREEN_LED_GPIO = 17   # your face
RED_LED_GPIO = 27     # another face
YELLOW_LED_GPIO = 23  # right hand up
BLUE_LED_GPIO = 22    # left hand up

green = LED(GREEN_LED_GPIO)
red = LED(RED_LED_GPIO)
yellow = LED(YELLOW_LED_GPIO)
blue = LED(BLUE_LED_GPIO)

# ----------------------------
# Face recognition files
# ----------------------------
MODEL_PATH = Path("trainer/me_lbph.yml")
CASCADE_PATH = "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"

# LBPH: lower confidence = better match
# If it does not recognize you, increase to 75.
# If it recognizes others as you, decrease to 55.
CONFIDENCE_THRESHOLD = 65

# ----------------------------
# Camera settings
# ----------------------------
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# ----------------------------
# Load OpenCV face detector
# ----------------------------
face_detector = cv2.CascadeClassifier(CASCADE_PATH)

if face_detector.empty():
    raise RuntimeError(f"Could not load Haar cascade from {CASCADE_PATH}")

if not MODEL_PATH.exists():
    raise RuntimeError("Model not found. Run 04_train_model.py first.")

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(str(MODEL_PATH))

# ----------------------------
# Load YOLO Pose model
# ----------------------------
# First run may download yolo11n-pose.pt
pose_model = YOLO("yolo11n-pose.pt")

# YOLO / COCO keypoint indexes:
# 5  = left shoulder
# 6  = right shoulder
# 9  = left wrist
# 10 = right wrist

LEFT_SHOULDER = 5
RIGHT_SHOULDER = 6
LEFT_WRIST = 9
RIGHT_WRIST = 10

# ----------------------------
# Start camera
# ----------------------------
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (FRAME_WIDTH, FRAME_HEIGHT), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()

time.sleep(2)

# ----------------------------
# LED helpers
# ----------------------------
def all_leds_off():
    green.off()
    red.off()
    yellow.off()
    blue.off()


def show_no_face():
    all_leds_off()


def show_unknown_face():
    green.off()
    red.on()
    yellow.off()
    blue.off()


def show_me(right_hand_up=False, left_hand_up=False):
    green.on()
    red.off()

    if right_hand_up:
        yellow.on()
    else:
        yellow.off()

    if left_hand_up:
        blue.on()
    else:
        blue.off()


# ----------------------------
# Face recognition
# ----------------------------
def recognize_face(frame_rgb):
    """
    Returns:
    - "NO_FACE"
    - "ME"
    - "UNKNOWN"
    """

    gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(80, 80)
    )

    if len(faces) == 0:
        return "NO_FACE"

    for (x, y, w, h) in faces:
        face = gray[y:y+h, x:x+w]
        face = cv2.resize(face, (200, 200))

        label, confidence = recognizer.predict(face)
        print(f"Face label={label}, confidence={confidence:.2f}")

        if label == 1 and confidence < CONFIDENCE_THRESHOLD:
            return "ME"

    return "UNKNOWN"


# ----------------------------
# Hand-up gesture detection
# ----------------------------
def detect_hands_up(frame_rgb):
    """
    Returns:
    right_hand_up, left_hand_up

    Important:
    YOLO keypoints use the person's body:
    - right hand = person's right hand
    - left hand = person's left hand

    If they appear reversed on camera, swap yellow and blue in the code.
    """

    results = pose_model(frame_rgb, conf=0.4, verbose=False)

    if len(results) == 0:
        return False, False

    result = results[0]

    if result.keypoints is None:
        return False, False

    keypoints_xy = result.keypoints.xy.cpu().numpy()

    if len(keypoints_xy) == 0:
        return False, False

    # Use the first detected person
    person = keypoints_xy[0]

    left_shoulder = person[LEFT_SHOULDER]
    right_shoulder = person[RIGHT_SHOULDER]
    left_wrist = person[LEFT_WRIST]
    right_wrist = person[RIGHT_WRIST]

    ls_x, ls_y = left_shoulder
    rs_x, rs_y = right_shoulder
    lw_x, lw_y = left_wrist
    rw_x, rw_y = right_wrist

    # If YOLO did not detect a keypoint, it may be 0,0
    if ls_x == 0 and ls_y == 0:
        return False, False

    if rs_x == 0 and rs_y == 0:
        return False, False

    # In image coordinates:
    # smaller y = higher in the image
    margin = 30

    right_hand_up = rw_y > 0 and rw_y < rs_y - margin
    left_hand_up = lw_y > 0 and lw_y < ls_y - margin

    return right_hand_up, left_hand_up


# ----------------------------
# Safe shutdown
# ----------------------------
def shutdown_handler(signum, frame):
    all_leds_off()
    picam2.stop()
    sys.exit(0)


signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

# ----------------------------
# Main loop
# ----------------------------
all_leds_off()

print("Running final ME project.")
print("No face              = all LEDs off")
print("Your face            = green")
print("Another face         = red")
print("Your + right hand up = green + yellow")
print("Your + left hand up  = green + blue")
print("Press Ctrl+C to stop.")

try:
    while True:
        frame_rgb = picam2.capture_array()

        identity = recognize_face(frame_rgb)

        if identity == "NO_FACE":
            print("State: NO_FACE")
            show_no_face()
            time.sleep(0.1)
            continue

        if identity == "UNKNOWN":
            print("State: UNKNOWN_FACE")
            show_unknown_face()
            time.sleep(0.1)
            continue

        # Only if your face is recognized, check gestures
        right_hand_up, left_hand_up = detect_hands_up(frame_rgb)

        print(
            f"State: ME | right_hand_up={right_hand_up} | left_hand_up={left_hand_up}"
        )

        show_me(
            right_hand_up=right_hand_up,
            left_hand_up=left_hand_up
        )

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Stopping.")

finally:
    all_leds_off()
    picam2.stop()
