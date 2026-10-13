from XRPLib.defaults import *

from machine import Pin, I2C
import time

# XRP / Pico -> PCA9685 I2C connection
# IO16 = SDA
# IO17 = SCL

i2c = I2C(
    0,
    scl=Pin(17),
    sda=Pin(16),
    freq=400000
)

PCA9685_ADDR = 0x40

MODE1 = 0x00
PRESCALE = 0xFE
LED0_ON_L = 0x06

# ==================================================
# Settings
# ==================================================

NUMBER_OF_SERVOS = 16
START_ANGLE = 90

MIN_ANGLE = 0
MAX_ANGLE = 180

SERVO_NAMES = [
    "FL_HIP",      # 0
    "FL_FEMUR",    # 1
    "FL_KNEE",     # 2

    "FR_HIP",      # 3
    "FR_FEMUR",    # 4
    "FR_KNEE",     # 5

    "RL_HIP",      # 6
    "RL_FEMUR",    # 7
    "RL_KNEE",     # 8

    "RR_HIP",      # 9
    "RR_FEMUR",    # 10
    "RR_KNEE",     # 11

    "TEST_12",     # 12
    "TEST_13",     # 13
    "TEST_14",     # 14
    "TEST_15"      # 15
]


# ==================================================
# PCA9685 basic functions
# ==================================================

def write_reg(reg, value):
    i2c.writeto_mem(PCA9685_ADDR, reg, bytes([value]))


def read_reg(reg):
    return i2c.readfrom_mem(PCA9685_ADDR, reg, 1)[0]


def set_pwm_freq(freq_hz):
    prescaleval = 25000000.0
    prescaleval = prescaleval / 4096.0
    prescaleval = prescaleval / freq_hz
    prescaleval = prescaleval - 1.0

    prescale = int(prescaleval + 0.5)

    oldmode = read_reg(MODE1)
    sleep_mode = (oldmode & 0x7F) | 0x10

    write_reg(MODE1, sleep_mode)
    write_reg(PRESCALE, prescale)
    write_reg(MODE1, oldmode)

    time.sleep(0.005)

    write_reg(MODE1, oldmode | 0xA1)


def set_pwm(channel, on, off):
    reg = LED0_ON_L + 4 * channel

    data = bytes([
        on & 0xFF,
        on >> 8,
        off & 0xFF,
        off >> 8
    ])

    i2c.writeto_mem(PCA9685_ADDR, reg, data)


def angle_to_count(angle):
    if angle < MIN_ANGLE:
        angle = MIN_ANGLE

    if angle > MAX_ANGLE:
        angle = MAX_ANGLE

    pulse_us = 500 + (angle / 180.0) * 2000
    count = int(pulse_us * 4096 / 20000)

    return count


def set_servo_angle(channel, angle):
    count = angle_to_count(angle)
    set_pwm(channel, 0, count)


def move_all_servos(angle):
    print("")
    print("Moving all channels 0-15 to", angle)

    for channel in range(NUMBER_OF_SERVOS):
        set_servo_angle(channel, angle)
        time.sleep(0.12)

    print("All channels moved to", angle)
    print("")


def print_servo_map():
    print("")
    print("Servo / Channel map")
    print("----------------")

    for channel in range(NUMBER_OF_SERVOS):
        print(str(channel) + " = " + SERVO_NAMES[channel])

    print("----------------")
    print("")


def print_current_angles(current_angles):
    print("")
    print("Current angles")
    print("----------------")

    for channel in range(NUMBER_OF_SERVOS):
        print(str(channel) + " " + SERVO_NAMES[channel] + " = " + str(current_angles[channel]))

    print("----------------")
    print("")


def initialize_pca9685():
    print("Initializing PCA9685")

    write_reg(MODE1, 0x00)
    set_pwm_freq(50)

    time.sleep(1)

    print("PCA9685 ready")


def print_menu():
    print("")
    print("Commands:")
    print("  Type servo channel 0-15 to move one servo")
    print("  Type m to show servo map")
    print("  Type a to show current angles")
    print("  Type r to reset all channels to 90")
    print("  Type q to quit")
    print("")


# ==================================================
# Main program
# ==================================================

initialize_pca9685()

current_angles = []

for i in range(NUMBER_OF_SERVOS):
    current_angles.append(START_ANGLE)

move_all_servos(START_ANGLE)

time.sleep(1)

print_servo_map()
print_current_angles(current_angles)
print_menu()

while True:
    try:
        servo_text = input("Command or servo number 0-15: ")

        if servo_text == "q" or servo_text == "Q":
            print("Program stopped")
            break

        if servo_text == "m" or servo_text == "M":
            print_servo_map()
            continue

        if servo_text == "a" or servo_text == "A":
            print_current_angles(current_angles)
            continue

        if servo_text == "r" or servo_text == "R":
            move_all_servos(START_ANGLE)

            for i in range(NUMBER_OF_SERVOS):
                current_angles[i] = START_ANGLE

            print_current_angles(current_angles)
            continue

        servo_number = int(servo_text)

        if servo_number < 0 or servo_number >= NUMBER_OF_SERVOS:
            print("Invalid servo number")
            print("Use a number from 0 to 15")
            print("")
            continue

        angle_text = input("Angle 0-180: ")
        angle = int(angle_text)

        if angle < MIN_ANGLE or angle > MAX_ANGLE:
            print("Invalid angle")
            print("Use angle from 0 to 180")
            print("")
            continue

        print("")
        print("Moving servo", servo_number, SERVO_NAMES[servo_number], "to", angle)

        set_servo_angle(servo_number, angle)

        current_angles[servo_number] = angle

        time.sleep(0.2)

        print("Done")
        print("")

    except ValueError:
        print("Please type a valid command or number")
        print("")

    except KeyboardInterrupt:
        print("")
        print("Stopped by keyboard")
        break