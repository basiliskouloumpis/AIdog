from picamera2 import Picamera2
import cv2
import time
from pathlib import Path

DATA_DIR = Path("dataset/me")
DATA_DIR.mkdir(parents=True, exist_ok=True)

TOTAL_IMAGES = 80

CASCADE_PATH = "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"

face_detector = cv2.CascadeClassifier(CASCADE_PATH)

if face_detector.empty():
    raise RuntimeError(f"Could not load Haar cascade from {CASCADE_PATH}")

picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()

time.sleep(2)

count = 0

print("Capturing your face images.")
print("Move your head slowly: center, left, right, up, down.")
print("Use different expressions and lighting if possible.")

while count < TOTAL_IMAGES:
    frame = picam2.capture_array()
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(80, 80)
    )

    if len(faces) > 0:
        # Use the largest detected face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

        face = gray[y:y+h, x:x+w]
        face = cv2.resize(face, (200, 200))

        filename = DATA_DIR / f"me_{count:03d}.jpg"
        cv2.imwrite(str(filename), face)

        count += 1
        print(f"Saved {count}/{TOTAL_IMAGES}: {filename}")

        time.sleep(0.15)

picam2.stop()

print("Done capturing face images.")
