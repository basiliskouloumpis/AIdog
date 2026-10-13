import subprocess
import time

PORT = "/dev/ttyACM0"  # change if yours is different

def run_on_xrp(code):
    """Send a snippet of Python to run directly on the XRP."""
    result = subprocess.run(
        ["python3", "-m", "mpremote", "connect", PORT, "exec", code],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("Error:", result.stderr)
    return result.stdout

def set_servo_angle(servo_name, angle):
    """servo_name should be 'servo_one' or 'servo_two'."""
    run_on_xrp(f"from XRPLib.defaults import *; {servo_name}.set_angle({angle})")

# --- Example usage ---
set_servo_angle("servo_one", 0)
time.sleep(1)

set_servo_angle("servo_two", 0)
time.sleep(1)

set_servo_angle("servo_one", 90)
set_servo_angle("servo_two", 90)
time.sleep(1)

set_servo_angle("servo_one", 180)
set_servo_angle("servo_two", 180)
time.sleep(1)
