# AI-Powered SpotMicro Robot Dog

**Technical documentation of a Raspberry Pi 5–XRP robotics prototype**  
**Communication:** Bluetooth Low Energy (BLE)  
**Document version:** 1.0 · 13 October 2026  
**Evidence base:** Python scripts, model file, and camera-test image supplied with the project

> **Implementation status.** This is documentation of the supplied prototype code, not a certification that every component has been deployed and tested together. Computer vision, LED feedback, Bluetooth command transmission, USB-based XRP servo experiments, and Raspberry Pi–PCA9685 servo experiments are represented in the files. The XRP-side BLE firmware and a complete vision-to-motion integration program were **not** supplied.

## 1. Project overview

The project aims to develop a small intelligent quadruped robot using a SpotMicro-style robotic dog platform. It combines the computational capabilities of a Raspberry Pi with an XRP robotics controller. The Raspberry Pi is intended to interpret visual information and make high-level decisions, while the XRP is intended to execute robot movement commands. Bluetooth Low Energy provides the planned wireless communication link between these controllers.

The code demonstrates an incremental development strategy: first verify the LEDs and camera; then collect facial images and train a face recognizer; add human-pose and gesture detection; build a browser-based vision diagnostic; and finally explore communication with the XRP and servo positioning. The resulting platform is designed as a foundation for person-aware and gesture-controlled robotic behavior.

**Primary goals**

- Recognize a previously enrolled person using the Raspberry Pi camera.
- Distinguish a recognized face from an unknown face, with immediate LED feedback.
- Detect raised left and right hands using AI-based human pose estimation.
- Determine the relative location of a person's nose within the camera view.
- Communicate commands from the Raspberry Pi to an XRP controller over BLE.
- Experiment with robotic servo control as a foundation for standing and walking behaviors.

## 2. System architecture

The intended architecture has two processing layers: high-level perception and command generation on the Raspberry Pi, and low-level action execution on the XRP. The source files additionally contain **two separate servo-control experiments**: one using the XRP over USB and another using a PCA9685 board directly from the Raspberry Pi. Their simultaneous use, electrical wiring, and division of servo ownership are not specified.

```text
                         CAMERA
                           |
                           v
                 +--------------------+
                 | Raspberry Pi 5     |
                 | - Picamera2        |
                 | - OpenCV / LBPH    |
                 | - YOLO11 Pose      |
                 | - Decision logic*  |
                 +--------------------+
                   |       |        |
                   |       |        +--> GPIO LEDs (status / gestures)
                   |       |
                   |       +-- BLE --> XRP_DOG / XRP controller
                   |                   (commands; receiver code missing)
                   |
                   +-- I2C bus 1 --> PCA9685 --> 12 servo channels
                       [separate direct-control experiment]

        Separate USB experiment:
        Raspberry Pi -- /dev/ttyACM0 / mpremote --> XRP
                                           --> servo_one / servo_two

        * A unified perception-to-BLE movement controller is proposed,
          but is not present in the uploaded code.
```

**Architecture note:** The BLE path is implemented as an interactive client that transmits typed commands. The existing vision scripts do not call that BLE client, and the provided files do not show the XRP receiving those commands or generating a gait.

## 3. Hardware and interfaces

| Element | Function | Source evidence / configuration |
|---|---|---|
| Raspberry Pi (identified as Pi 5 in servo comments) | Camera processing, local AI inference, GPIO, communication | `allservos90.py` comment; multiple Python programs |
| Raspberry Pi camera | Captures visual frames | Picamera2, RGB888, 640 × 480 |
| XRP controller | Intended robotic motion controller | BLE device name `XRP_DOG`; `XRPLib` servo experiments |
| SpotMicro mechanical platform | Quadruped robot chassis and legs | `allservos90.py` specifies 12 leg servos |
| GPIO indicator LEDs | Identity and gesture feedback | GPIO 17 green, 27 red, 23 yellow, 22 blue |
| PCA9685 PWM board | Direct multichannel servo positioning experiment | I²C bus 1, address `0x40`, 50 Hz, channels 0–11 |
| Bluetooth Low Energy | Raspberry Pi to XRP command link | `bleak` client and fixed GATT characteristic UUIDs |
| USB serial connection | Alternative XRP development/control link | `/dev/ttyACM0` using `mpremote` |

**Unconfirmed hardware details:** The exact XRP variant, BLE peripheral implementation, wiring diagram, servo models, motor power distribution, joint-to-channel mapping, battery specifications, and final controller-to-servo topology are not contained in the supplied source files.

## 4. Software stack and data assets

The Raspberry Pi software is written in Python; `.python-version` specifies **Python 3.12.8**. The scripts use:

- **Picamera2** for camera configuration and frame acquisition.
- **OpenCV** for image conversion, Haar cascade face detection, drawing annotations, and the LBPH recognizer (`cv2.face`).
- **NumPy** for face-recognition training labels.
- **Ultralytics YOLO** for human pose/keypoint estimation; the model asset is `yolo11n-pose.pt`.
- **gpiozero** for LED status signals.
- **Flask** for a local HTTP video stream.
- **Bleak** for Bluetooth Low Energy device discovery, GATT connection, writes, and notifications.
- **smbus2** for I²C communication with the PCA9685 servo controller.
- **mpremote** for transmitting short MicroPython statements to the XRP over USB; the statements import `XRPLib.defaults` on the controller.

The uploads do not include a `requirements.txt`, installation script, or version-locked dependencies. `camera_test.jpg` is an output artifact of a camera test; the facial dataset (`dataset/me/`) and trained recognizer (`trainer/me_lbph.yml`) are referenced in code but were not included among the supplied files.

## 5. Development modules and source-file map

| File | Role | Status shown by source |
|---|---|---|
| `01_test_leds.py` | Alternates green and red GPIO LEDs once per second. | Standalone hardware test |
| `02_test_camera.py` | Captures a single camera image and writes `camera_test.jpg`. | Standalone camera test |
| `03_capture_me.py` | Detects and saves up to 80 cropped face images. | Data-acquisition program |
| `04_train_model.py` | Trains and saves a one-person LBPH face recognizer. | Offline training program |
| `05_run_recognition_leds.py` | Uses the camera and trained model to control red/green LEDs. | Live facial-recognition program |
| `07_me_face_hands_leds.py` | Adds YOLO pose-based left/right hand detection and four LED indicators. | Live face/gesture prototype |
| `08_view_nose_target.py` | Displays a nose target and offsets in a browser video feed. | Visual tracking diagnostic |
| `09_sendΒΤ.py` | BLE terminal client sending manually entered strings to `XRP_DOG`. | Wireless communication test |
| `09_sendΒΤ` | Same contents as `09_sendΒΤ.py`, without extension. | Duplicate BLE client |
| `allservos90.py` | Directly sets PCA9685 channels 0–11 to 90°. | Standalone 12-servo alignment test |
| `servo_control.py` | Uses USB/`mpremote` to set `servo_one` and `servo_two` on XRP. | Standalone 2-servo XRP test |
| `untitled` | Earlier USB/`mpremote` test of `servo_one`. | Standalone prototype |
| `yolo11n-pose.pt` | YOLO11 nano pose model asset. | Provided model file |
| `.python-version` | Specifies Python version `3.12.8`. | Environment metadata |
| `camera_test.jpg` | Camera capture sample (640 × 480). | Provided output image |

The numbering skips `06`; no script with that number was provided. The table reports what the code is written to do and does not imply physical test results where none were supplied.

## 6. Face enrollment and recognition

### 6.1 Capture an enrolled person's face

`03_capture_me.py` starts a Picamera2 preview configuration at 640 × 480 pixels and uses OpenCV's frontal-face Haar cascade located at `/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml`.

For each frame, the program converts RGB to grayscale and searches for faces (`scaleFactor=1.2`, `minNeighbors=5`, minimum region 80 × 80). If several faces are present, it selects the **largest** detected face, crops it, resizes it to **200 × 200** pixels, and saves the image as `dataset/me/me_000.jpg`, `me_001.jpg`, etc. The target is **80** saved face images, with a short 0.15-second delay between captures. The capture instructions recommend variation in head pose, facial expression, and lighting.

### 6.2 Train the recognition model

`04_train_model.py` loads all JPEG images from `dataset/me`, resizes them to 200 × 200, and trains an OpenCV **Local Binary Patterns Histograms (LBPH)** face recognizer. Training parameters are `radius=1`, `neighbors=8`, `grid_x=8`, and `grid_y=8`. Every training sample is assigned **label 1**, representing the enrolled person. The model is saved to `trainer/me_lbph.yml`.

This is a **single-enrolled-person** approach. It does not include a dataset of known nonmatches, biometric liveness checks, or formal accuracy validation.

### 6.3 Live recognition with LED indicators

`05_run_recognition_leds.py` detects faces in each camera frame and submits each detected face crop to the LBPH recognizer. If any detection returns `label == 1` with a score **below 65**, the green LED turns on; otherwise, the red LED turns on. In OpenCV LBPH terminology a **lower score indicates a closer match**; the constant named `CONFIDENCE_THRESHOLD` is therefore a distance-like decision threshold, not a probability.

| Camera result | LED behavior |
|---|---|
| No face detected | Both LEDs off |
| Enrolled face accepted | Green LED on, red off |
| Face(s) detected, none accepted | Red LED on, green off |

The threshold of 65 is a manually selected setting and has not been validated against false-positive and false-negative rates in the uploads.

## 7. Human pose estimation and gesture recognition

`07_me_face_hands_leds.py` combines the existing face recognizer with Ultralytics `YOLO("yolo11n-pose.pt")`. Its main loop checks identity first. Pose inference is performed **only when the face-recognition routine returns `ME`**. This reduces unnecessary pose processing for absent or unknown faces.

YOLO supplies COCO-style body keypoints. The code uses left shoulder **5**, right shoulder **6**, left wrist **9**, and right wrist **10**. In image coordinates, a smaller y value means a higher position. A hand is treated as raised if its wrist is at least **30 pixels above the corresponding shoulder**. The YOLO prediction threshold is `conf=0.4`.

| Detected state | Visual response |
|---|---|
| No face | All four LEDs off |
| Unknown face | Red LED on; other LEDs off |
| Enrolled face, no hand raised | Green LED on |
| Enrolled face, right hand raised | Green + yellow LEDs on |
| Enrolled face, left hand raised | Green + blue LEDs on |
| Enrolled face, both hands raised | Green + yellow + blue LEDs on |

**Important multi-person limitation:** Face recognition searches all visible faces, but pose estimation uses **the first person returned by YOLO**. The code does not geometrically associate the recognized face with that particular pose. In a multi-person scene, gestures can therefore be attributed to the wrong individual. The software should associate face bounding boxes and person detections before using gestures as motion commands.

The program has SIGINT/SIGTERM handlers and a final cleanup path to switch off the LEDs and stop the camera.

## 8. Nose tracking and browser diagnostics

`08_view_nose_target.py` uses the same YOLO11 pose model to locate keypoint **0 (nose)** on the first detected person. It overlays a center cross, a circle around the nose, a line connecting the camera center to the nose, and numerical position/error readouts.

For a 640 × 480 image, the target center is **(320, 240)**. The positional errors are calculated as:

`error_x = nose_x - 320`  
`error_y = nose_y - 240`

The code classifies the target's horizontal position as `LEFT`, `CENTER`, or `RIGHT` using a ±60-pixel deadband, and vertical position as `UP`, `CENTER`, or `DOWN` using a ±50-pixel deadband. If no valid nose keypoint is found, the frame shows `NO NOSE DETECTED`.

Flask serves a live multipart JPEG stream at `/video` and an HTML viewer at `/`, using port **8080**. The page can be accessed locally at `http://127.0.0.1:8080` or, where network access permits, at `http://<RASPBERRY_PI_IP>:8080`.

**Current scope:** This module visualizes a target and computes directional error; it does **not** transmit tracking adjustments to servos or automatically turn the robot. It binds to all network interfaces (`0.0.0.0`) without an authentication mechanism in the supplied code, so it should be restricted to a trusted network.

## 9. Bluetooth Low Energy communication

The BLE client in `09_sendΒΤ.py` uses Bleak to search for a device with the exact advertised name **`XRP_DOG`**. The discovery timeout is **5 seconds**. If a matching device is found, the program connects, subscribes to notifications on one GATT characteristic, and writes text commands to another characteristic.

| Setting | Value |
|---|---|
| BLE target name | `XRP_DOG` |
| Write characteristic (`RX_UUID`) | `6E400002-B5A3-F393-E0A9-E50E24DCCA9E` |
| Notification characteristic (`TX_UUID`) | `6E400003-B5A3-F393-E0A9-E50E24DCCA9E` |
| User command examples in prompt | `CRAWL`, `STAND`, `TEST`, `PING` |
| Exit command | `q` |
| Data encoding | UTF-8 |

A command is collected from the terminal and sent with `write_gatt_char(...)`. Any received notification is printed as text prefixed with `XRP:`. These UUIDs are consistent with a Nordic UART-style BLE characteristic arrangement, but the full GATT service definition and **XRP firmware were not included**, so actual device support cannot be independently confirmed from the supplied material.

The command names appear in the input prompt; **their actions are not defined in the client file**. In particular, `CRAWL` and `STAND` are not proof that a working gait controller is already implemented.

**Technical issue to review:** The use of synchronous `input()` inside an `async` event loop can delay BLE notification processing until terminal input returns. A nonblocking input strategy or a dedicated input thread would make interactive communication more robust.

## 10. Servo control experiments

### 10.1 Raspberry Pi → PCA9685 → 12 servos

`allservos90.py` communicates directly with a PCA9685 board over **I²C bus 1**, using default address **0x40**. It configures a **50 Hz** PWM frequency and sends servo-position pulses on **channels 0 through 11**, positioning each servo at a commanded **90 degrees** with a 0.1-second delay between channels. It then remains running, holding the target positions.

The conversion assumes a nominal pulse width of **500 microseconds at 0°** and **2500 microseconds at 180°**, with a linear interpolation between. These are program assumptions, not verified safe endpoints for the actual servos or leg mechanism.

**Scope:** This script tests central positioning of twelve servos. It contains no gait sequencing, inverse kinematics, joint calibration, mechanically constrained limit table, or motion interpolation. Its servo path is driven **directly by the Pi**, not shown as being controlled through BLE or XRP.

### 10.2 Raspberry Pi → USB → XRP → two servos

`servo_control.py` uses `python3 -m mpremote` and port `/dev/ttyACM0` to execute snippets on the XRP. Those snippets call `servo_one.set_angle(...)` or `servo_two.set_angle(...)` after importing `XRPLib.defaults` in the XRP's MicroPython environment. The example commands move those two named servos through **0°, 90°, and 180°** in sequence.

The separate `untitled` script is an earlier one-servo variant using `mpremote` directly. These are **USB-based development/control methods**, not Bluetooth control routines. They also do not specify the complete twelve-joint arrangement of the SpotMicro.

**Mechanical safety:** A fixed 90° starting position or a sweep to 0°/180° may be unsuitable for a particular joint installation. Before energizing the assembled robot, calibrate joint direction and physical limits, support the chassis, verify power distribution and common ground as appropriate, and introduce controlled motion limits.

## 11. Recommended reproduction sequence

The following sequence reflects the dependencies visible in the code. It is a **recommended procedure**, not a claim that a fully automated installation workflow exists.

1. **Prepare hardware and Python environment.** Verify camera connectivity, GPIO LED wiring, the Pi's I²C interface if using PCA9685, and the separate XRP connection. Use the Python version indicated in `.python-version` if compatible with the installed Raspberry Pi packages.
2. **Verify LEDs:** run `python3 01_test_leds.py`. The green and red indicators should alternate each second.
3. **Verify the camera:** run `python3 02_test_camera.py`. Confirm that `camera_test.jpg` is generated at 640 × 480.
4. **Capture training data:** run `python3 03_capture_me.py`. Collect the 80 intended face samples in `dataset/me`.
5. **Train the recognizer:** run `python3 04_train_model.py`. Confirm the generated `trainer/me_lbph.yml` file.
6. **Test identity recognition:** run `python3 05_run_recognition_leds.py` and assess unknown/known face behavior.
7. **Test gestures:** run `python3 07_me_face_hands_leds.py`, with `yolo11n-pose.pt` present in the working directory.
8. **Inspect camera target tracking:** run `python3 08_view_nose_target.py` and visit the local web viewer on port 8080.
9. **Test wireless connectivity:** run `python3 '09_sendΒΤ.py'` after confirming that the XRP advertises `XRP_DOG` and provides the required BLE characteristics; type `PING` or other supported commands.
10. **Perform separate, cautious servo tests:** use `servo_control.py` for USB-connected XRP servo exercises, or `allservos90.py` for the standalone Pi/PCA9685 setup **only after hardware calibration**.

Most script paths, the trained-model location, and the YOLO model filename are **relative to the current working directory**; run programs from the project directory unless paths are adapted. Required Python modules are implied by the imports and include `gpiozero`, `picamera2`, OpenCV with `cv2.face`, `numpy`, `ultralytics`, `flask`, `bleak`, `smbus2`, and `mpremote` where applicable. Raspberry Pi camera/GPIO packages may require system-specific installation rather than a single universal `pip` command.

## 12. Proposed end-to-end behavior (not yet implemented)

A logical next iteration would connect the already prototyped perception modules to an XRP motion controller:

1. Acquire a camera frame and detect the person of interest.
2. Verify identity; associate the accepted face with the corresponding YOLO person detection.
3. Classify an intentional hand gesture or another high-level instruction.
4. Translate that event into a bounded motion command, such as `STAND`, `CRAWL`, or `STOP`.
5. Send the command over BLE with a defined message format and acknowledgement.
6. Validate and execute the command in XRP firmware using a calibrated SpotMicro gait controller.
7. Report execution state and faults back to the Raspberry Pi; stop motion safely on communication loss.

This is a **proposed architecture**, not the current execution path in the uploaded programs. A particular gesture-to-motion mapping has not been implemented, and the meaning of available movement commands requires an XRP-side definition.

## 13. Current limitations and development priorities

| Priority | Gap observed in the source | Suggested next step |
|---|---|---|
| High | XRP-side BLE peripheral/command parser is absent. | Supply and document the actual XRP firmware and GATT service. |
| High | Vision output does not initiate BLE motion commands. | Implement one integration controller and an explicit state machine. |
| High | Three experimental servo paths lack a documented final ownership model. | Choose one controller for each joint, define pin/channel mapping, and produce wiring documentation. |
| High | Joint calibration and movement failsafes are not shown. | Add calibrated bounds, speed limits, emergency stop, and link-loss behavior. |
| High | Gesture pose may belong to a different person than the recognized face. | Associate the face with the correct pose/person before command generation. |
| Medium | Face identification uses one enrolled class and a manual LBPH threshold. | Evaluate error rates across subjects, distances, and lighting conditions. |
| Medium | BLE client blocks its event loop while waiting for input. | Move input handling off the event loop or redesign as a queued client. |
| Medium | Web viewer has no access-control implementation. | Limit exposure to a trusted network and add access controls if needed. |
| Medium | No automated dependency or integration tests are included. | Add versioned dependencies, structured logging, and repeatable tests. |

## 14. Suggested verification checklist

These are proposed **acceptance tests**, not reported test results.

- [ ] The Raspberry Pi detects and captures camera frames reliably.
- [ ] GPIO indicators reproduce the defined recognition and gesture state table.
- [ ] Enrollment and LBPH training can be repeated from a clean project directory.
- [ ] The system avoids recognizing an unknown individual as the enrolled operator in representative tests.
- [ ] Raised hands are associated with the enrolled person when more than one person is visible.
- [ ] The XRP advertises as `XRP_DOG` with the expected GATT characteristics.
- [ ] A BLE `PING` request receives a documented, correctly framed response.
- [ ] Supported movement commands produce the intended motion and a response code.
- [ ] Robot joints remain inside calibrated ranges during standing and locomotion.
- [ ] BLE disconnection or perception failure triggers the designed safe behavior.

## 15. Conclusion

The supplied code establishes several essential building blocks for an intelligent SpotMicro robot: Raspberry Pi camera acquisition, enrollment-based face recognition, AI human-pose interpretation, LED feedback, visual tracking diagnostics, BLE command transmission, and independent servo-control experiments. Together, they support a clear **high-level perception / low-level actuation** design direction.

The main engineering milestone still to be documented and integrated is the **closed-loop connection from perception to validated XRP motion commands and safe twelve-servo quadruped control**. Achieving that milestone would turn the existing component prototypes into a cohesive person-aware robotic-dog system.


**Evidence boundary:** The documentation is based on the files supplied for this project. XRP-side BLE firmware, a full wiring diagram, a trained face-recognition artifact, gait-control code, and integrated test logs were not provided.
