from picamera2 import Picamera2
import cv2
import time

picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)

picam2.configure(config)
picam2.start()

time.sleep(2)

frame = picam2.capture_array()

# Save a test image
frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
cv2.imwrite("camera_test.jpg", frame_bgr)

picam2.stop()

print("Saved camera_test.jpg")
