import time
from smbus2 import SMBus

# ==================================================
# Raspberry Pi 5 uses I2C bus 1
# PCA9685 default address is 0x40
# ==================================================

I2C_BUS = 1
PCA9685_ADDR = 0x40

MODE1 = 0x00
PRESCALE = 0xFE
LED0_ON_L = 0x06

NUMBER_OF_SERVOS = 12   # use 12 for SpotMicro legs, channels 0-11
TARGET_ANGLE = 90


bus = SMBus(I2C_BUS)


# ==================================================
# PCA9685 basic functions
# ==================================================

def write_reg(reg, value):
    bus.write_byte_data(PCA9685_ADDR, reg, value)


def read_reg(reg):
    return bus.read_byte_data(PCA9685_ADDR, reg)


def set_pwm_freq(freq_hz):
    prescaleval = 25000000.0
    prescaleval /= 4096.0
    prescaleval /= freq_hz
    prescaleval -= 1.0

    prescale = int(prescaleval + 0.5)

    oldmode = read_reg(MODE1)
    sleep_mode = (oldmode & 0x7F) | 0x10

    write_reg(MODE1, sleep_mode)
    write_reg(PRESCALE, prescale)
    write_reg(MODE1, oldmode)

    time.sleep(0.005)

    # Restart + auto-increment
    write_reg(MODE1, oldmode | 0xA1)


def set_pwm(channel, on, off):
    reg = LED0_ON_L + 4 * channel

    data = [
        on & 0xFF,
        on >> 8,
        off & 0xFF,
        off >> 8
    ]

    bus.write_i2c_block_data(PCA9685_ADDR, reg, data)


def angle_to_count(angle):
    if angle < 0:
        angle = 0

    if angle > 180:
        angle = 180

    # Typical servo pulse range:
    # 0 degrees   = 500 us
    # 180 degrees = 2500 us
    pulse_us = 500 + (angle / 180.0) * 2000

    # PCA9685 at 50Hz:
    # period = 20,000 us
    count = int(pulse_us * 4096 / 20000)

    return count


def set_servo_angle(channel, angle):
    count = angle_to_count(angle)
    set_pwm(channel, 0, count)


def disable_servo(channel):
    set_pwm(channel, 0, 0)


def disable_all_servos():
    for channel in range(16):
        disable_servo(channel)
        time.sleep(0.02)


# ==================================================
# Main
# ==================================================

print("Initializing PCA9685...")

write_reg(MODE1, 0x00)
set_pwm_freq(50)

time.sleep(1)

print("Moving all SpotMicro servos to 90 degrees...")

for channel in range(NUMBER_OF_SERVOS):
    print("Servo", channel, "->", TARGET_ANGLE, "degrees")
    set_servo_angle(channel, TARGET_ANGLE)
    time.sleep(0.1)

print("All servos are holding at 90 degrees.")

while True:
    time.sleep(1)
