from picamera2 import Picamera2
from ultralytics import YOLO
from flask import Flask, Response
import cv2
import time
import signal
import sys

# ----------------------------
# Camera settings
# ----------------------------
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# YOLO Pose keypoint index
NOSE = 0

# Detection settings
CONFIDENCE = 0.4
CENTER_TOLERANCE_X = 60
CENTER_TOLERANCE_Y = 50

# ----------------------------
# Load YOLO Pose model
# ----------------------------
pose_model = YOLO("yolo11n-pose.pt")

# ----------------------------
# Start camera
# ----------------------------
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={
        "size": (FRAME_WIDTH, FRAME_HEIGHT),
        "format": "RGB888"
    }
)
picam2.configure(config)
picam2.start()

time.sleep(2)

# ----------------------------
# Flask app
# ----------------------------
app = Flask(__name__)


def get_nose_position(frame_rgb):
    results = pose_model(frame_rgb, conf=CONFIDENCE, verbose=False)

    if not results:
        return None, None

    result = results[0]

    if result.keypoints is None:
        return None, None

    keypoints = result.keypoints.xy.cpu().numpy()

    if len(keypoints) == 0:
        return None, None

    person = keypoints[0]
    nose_x, nose_y = person[NOSE]

    if nose_x <= 0 or nose_y <= 0:
        return None, None

    return int(nose_x), int(nose_y)


def get_direction(nose_x, nose_y):
    center_x = FRAME_WIDTH // 2
    center_y = FRAME_HEIGHT // 2

    error_x = nose_x - center_x
    error_y = nose_y - center_y

    if error_x < -CENTER_TOLERANCE_X:
        horizontal = "LEFT"
    elif error_x > CENTER_TOLERANCE_X:
        horizontal = "RIGHT"
    else:
        horizontal = "CENTER"

    if error_y < -CENTER_TOLERANCE_Y:
        vertical = "UP"
    elif error_y > CENTER_TOLERANCE_Y:
        vertical = "DOWN"
    else:
        vertical = "CENTER"

    return horizontal, vertical, error_x, error_y


def create_annotated_frame():
    frame_rgb = picam2.capture_array()
    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

    center_x = FRAME_WIDTH // 2
    center_y = FRAME_HEIGHT // 2

    # Draw center cross
    cv2.drawMarker(
        frame_bgr,
        (center_x, center_y),
        (255, 255, 255),
        markerType=cv2.MARKER_CROSS,
        markerSize=30,
        thickness=2
    )

    nose_x, nose_y = get_nose_position(frame_rgb)

    if nose_x is None or nose_y is None:
        cv2.putText(
            frame_bgr,
            "NO NOSE DETECTED",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )
    else:
        horizontal, vertical, error_x, error_y = get_direction(nose_x, nose_y)

        # Draw nose target
        cv2.circle(frame_bgr, (nose_x, nose_y), 14, (0, 255, 0), 2)
        cv2.circle(frame_bgr, (nose_x, nose_y), 4, (0, 255, 0), -1)

        # Draw line from center to nose
        cv2.line(
            frame_bgr,
            (center_x, center_y),
            (nose_x, nose_y),
            (0, 255, 255),
            2
        )

        cv2.putText(
            frame_bgr,
            f"Nose: x={nose_x}, y={nose_y}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame_bgr,
            f"Error: x={error_x}, y={error_y}",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2
        )

        cv2.putText(
            frame_bgr,
            f"Direction: {horizontal} / {vertical}",
            (20, 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 0),
            2
        )

    return frame_bgr


def generate_frames():
    while True:
        frame = create_annotated_frame()

        success, buffer = cv2.imencode(".jpg", frame)

        if not success:
            continue

        jpg_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            jpg_bytes +
            b"\r\n"
        )


@app.route("/")
def index():
    return """
    <html>
        <head>
            <title>YOLO Pose Nose Target</title>
        </head>
        <body style="background:#111; color:white; text-align:center; font-family:Arial;">
            <h1>YOLO Pose Nose Target</h1>
            <p>Green circle = nose | White cross = camera center | Yellow line = offset</p>
            <img src="/video" width="640" height="480">
        </body>
    </html>
    """


@app.route("/video")
def video():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


def stop_program():
    picam2.stop()


def shutdown_handler(signum, frame):
    stop_program()
    sys.exit(0)


signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)


if __name__ == "__main__":
    print("Starting web camera viewer.")
    print("Open this in a browser:")
    print("http://127.0.0.1:8080")
    print("or from another device:")
    print("http://<RASPBERRY_PI_IP>:8080")
    app.run(host="0.0.0.0", port=8080, threaded=True)
