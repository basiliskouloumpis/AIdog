import cv2
import numpy as np
from pathlib import Path

DATA_DIR = Path("dataset/me")
TRAINER_DIR = Path("trainer")
TRAINER_DIR.mkdir(exist_ok=True)

if not hasattr(cv2, "face"):
    raise RuntimeError(
        "cv2.face is missing. Install opencv-contrib-python-headless."
    )

faces = []
labels = []

# Label 1 means "me"
MY_LABEL = 1

image_files = sorted(DATA_DIR.glob("*.jpg"))

if len(image_files) == 0:
    raise RuntimeError("No face images found. Run 03_capture_me.py first.")

for image_path in image_files:
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

    if img is None:
        continue

    img = cv2.resize(img, (200, 200))

    faces.append(img)
    labels.append(MY_LABEL)

recognizer = cv2.face.LBPHFaceRecognizer_create(
    radius=1,
    neighbors=8,
    grid_x=8,
    grid_y=8
)

recognizer.train(faces, np.array(labels))
recognizer.write(str(TRAINER_DIR / "me_lbph.yml"))

print(f"Trained with {len(faces)} images.")
print("Saved model to trainer/me_lbph.yml")
