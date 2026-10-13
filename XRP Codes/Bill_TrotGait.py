from XRPLib.defaults import *

# available variables from defaults: left_motor, right_motor, drivetrain,
#      imu, rangefinder, reflectance, servo_one, board, webserver
# Write your code Here

from XRPLib.defaults import *

from machine import Pin, I2C
import time

# ==================================================
# XRP to PCA9685
# IO16 = SDA
# IO17 = SCL
# Trot gait version
# ==================================================

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
# Servo map
# ==================================================
# 0  = FL_HIP
# 1  = FL_FEMUR
# 2  = FL_KNEE
# 3  = FR_HIP
# 4  = FR_FEMUR
# 5  = FR_KNEE
# 6  = RL_HIP
# 7  = RL_FEMUR
# 8  = RL_KNEE
# 9  = RR_HIP
# 10 = RR_FEMUR
# 11 = RR_KNEE

FL_HIP = 0
FL_FEMUR = 1
FL_KNEE = 2

FR_HIP = 3
FR_FEMUR = 4
FR_KNEE = 5

RL_HIP = 6
RL_FEMUR = 7
RL_KNEE = 8

RR_HIP = 9
RR_FEMUR = 10
RR_KNEE = 11

# ==================================================
# Neutral / balance angles
# These are your current tested balance values
# ==================================================

NEUTRAL = [
    90, 110, 140,    # FL: hip, femur, knee
    80,  70,  40,    # FR: hip, femur, knee
    90, 110, 140,    # RL: hip, femur, knee
    90,  70,  40     # RR: hip, femur, knee
]

# ==================================================
# Servo direction
# Change 1 to -1 if a servo moves wrong way
# ==================================================

DIR = [
     1, -1,  1,    # FL
    -1,  1, -1,    # FR
     1, -1,  1,    # RL
    -1,  1, -1     # RR
]

# ==================================================
# Trot gait settings
# Start smaller than crawl because two legs move together
# ==================================================

HIP_SWING = 10
FEMUR_LIFT = 12
KNEE_BEND = 14

MIN_ANGLE = 20
MAX_ANGLE = 160

SMOOTH_STEPS = 6
STEP_DELAY = 0.025
PHASE_DELAY = 0.08

NUMBER_OF_STEPS = 5

# Trot pairs
PAIR_A = ["FL", "RR"]
PAIR_B = ["FR", "RL"]


# ==================================================
# PCA9685 functions
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


def corrected_angle(channel, target_angle):
    neutral = NEUTRAL[channel]
    difference = target_angle - neutral
    real_angle = neutral + DIR[channel] * difference

    if real_angle < MIN_ANGLE:
        real_angle = MIN_ANGLE

    if real_angle > MAX_ANGLE:
        real_angle = MAX_ANGLE

    return real_angle


# ==================================================
# Pose functions
# ==================================================

def set_pose(pose):
    for channel in range(12):
        angle = corrected_angle(channel, pose[channel])
        set_servo_angle(channel, angle)
        time.sleep(0.005)


def smooth_move(start_pose, end_pose, steps):
    for step in range(1, steps + 1):
        pose = []

        for i in range(12):
            value = start_pose[i] + (end_pose[i] - start_pose[i]) * step / steps
            pose.append(value)

        set_pose(pose)
        time.sleep(STEP_DELAY)


def neutral_pose():
    return [
        NEUTRAL[0], NEUTRAL[1], NEUTRAL[2],
        NEUTRAL[3], NEUTRAL[4], NEUTRAL[5],
        NEUTRAL[6], NEUTRAL[7], NEUTRAL[8],
        NEUTRAL[9], NEUTRAL[10], NEUTRAL[11]
    ]


def stand():
    pose = neutral_pose()
    set_pose(pose)
    return pose


# ==================================================
# Leg helpers
# ==================================================

def leg_channels(leg_name):
    if leg_name == "FL":
        return FL_HIP, FL_FEMUR, FL_KNEE

    if leg_name == "FR":
        return FR_HIP, FR_FEMUR, FR_KNEE

    if leg_name == "RL":
        return RL_HIP, RL_FEMUR, RL_KNEE

    if leg_name == "RR":
        return RR_HIP, RR_FEMUR, RR_KNEE

    return FL_HIP, FL_FEMUR, FL_KNEE


def lift_leg_in_pose(pose, leg_name):
    hip, femur, knee = leg_channels(leg_name)

    pose[femur] = NEUTRAL[femur] - FEMUR_LIFT
    pose[knee] = NEUTRAL[knee] + KNEE_BEND


def swing_leg_forward_in_pose(pose, leg_name):
    hip, femur, knee = leg_channels(leg_name)

    pose[hip] = NEUTRAL[hip] + HIP_SWING
    pose[femur] = NEUTRAL[femur] - FEMUR_LIFT
    pose[knee] = NEUTRAL[knee] + KNEE_BEND


def place_leg_in_pose(pose, leg_name):
    hip, femur, knee = leg_channels(leg_name)

    pose[hip] = NEUTRAL[hip] + HIP_SWING
    pose[femur] = NEUTRAL[femur]
    pose[knee] = NEUTRAL[knee]


def return_leg_neutral_in_pose(pose, leg_name):
    hip, femur, knee = leg_channels(leg_name)

    pose[hip] = NEUTRAL[hip]
    pose[femur] = NEUTRAL[femur]
    pose[knee] = NEUTRAL[knee]


# ==================================================
# Trot pair movement
# ==================================================

def lift_pair_pose(base_pose, pair):
    pose = base_pose[:]

    for leg in pair:
        lift_leg_in_pose(pose, leg)

    return pose


def swing_pair_forward_pose(base_pose, pair):
    pose = base_pose[:]

    for leg in pair:
        swing_leg_forward_in_pose(pose, leg)

    return pose


def place_pair_pose(base_pose, pair):
    pose = base_pose[:]

    for leg in pair:
        place_leg_in_pose(pose, leg)

    return pose


def return_pair_neutral_pose(base_pose, pair):
    pose = base_pose[:]

    for leg in pair:
        return_leg_neutral_in_pose(pose, leg)

    return pose


def step_pair(current_pose, pair_name, pair):
    print("Pair:", pair_name)

    # 1. Lift diagonal pair
    next_pose = lift_pair_pose(current_pose, pair)
    smooth_move(current_pose, next_pose, SMOOTH_STEPS)
    time.sleep(PHASE_DELAY)

    # 2. Swing diagonal pair forward
    current_pose = next_pose
    next_pose = swing_pair_forward_pose(current_pose, pair)
    smooth_move(current_pose, next_pose, SMOOTH_STEPS)
    time.sleep(PHASE_DELAY)

    # 3. Place pair down
    current_pose = next_pose
    next_pose = place_pair_pose(current_pose, pair)
    smooth_move(current_pose, next_pose, SMOOTH_STEPS)
    time.sleep(PHASE_DELAY)

    # 4. Return pair to neutral
    current_pose = next_pose
    next_pose = return_pair_neutral_pose(current_pose, pair)
    smooth_move(current_pose, next_pose, SMOOTH_STEPS)
    time.sleep(PHASE_DELAY)

    return next_pose


# ==================================================
# Main program
# ==================================================

print("Init PCA9685")

write_reg(MODE1, 0x00)
set_pwm_freq(50)

time.sleep(1)

print("Stand")
current_pose = stand()
time.sleep(1)

print("Start trot gait")
print("Pair A = FL + RR")
print("Pair B = FR + RL")

for step_number in range(NUMBER_OF_STEPS):
    print("Cycle:", step_number + 1)

    current_pose = step_pair(current_pose, "A FL+RR", PAIR_A)
    current_pose = step_pair(current_pose, "B FR+RL", PAIR_B)

print("Done")
stand()

while True:
    time.sleep(1)