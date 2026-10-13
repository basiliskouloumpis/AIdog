from picamera2 import Picamera2
from gpiozero import LED
import cv2
import time
from pathlib import Path

GREEN_LED_GPIO = 17
RED_LED_GPIO = 27

MODEL_PATH = Path("trainer/me_lbph.yml")
CASCADE_PATH = "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"

# For LBPH: lower confidence = better match
CONFIDENCE_THRESHOLD = 65

green = LED(GREEN_LED_GPIO)
red = LED(RED_LED_GPIO)

face_detector = cv2.CascadeClassifier(CASCADE_PATH)
if face_detector.empty():
    raise RuntimeError(f"Could not load Haar cascade from {CASCADE_PATH}")

if not MODEL_PATH.exists():
    raise RuntimeError("Model not found. Run 04_train_model.py first.")

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(str(MODEL_PATH))

picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()

time.sleep(2)

def leds_off():
    green.off()
    red.off()

def set_green():
    green.on()
    red.off()

def set_red():
    green.off()
    red.on()

leds_off()

print("Running face recognition.")
print("No face      = no LED")
print("Unknown face = red LED")
print("Your face    = green LED")
print("Press Ctrl+C to stop.")

try:
    while True:
        frame = picam2.capture_array()
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

        faces = face_detector.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(80, 80)
        )

        # State 1: no face
        if len(faces) == 0:
            leds_off()
            time.sleep(0.1)
            continue

        recognized_me = False

        # Check all detected faces
        for (x, y, w, h) in faces:
            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, (200, 200))

            label, confidence = recognizer.predict(face)
            print(f"label={label}, confidence={confidence:.2f}")

            if label == 1 and confidence < CONFIDENCE_THRESHOLD:
                recognized_me = True
                break

        # State 2 and 3
        if recognized_me:
            set_green()
        else:
            set_red()

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Stopping.")

finally:
    leds_off()
    picam2.stop()
