from gpiozero import LED
from time import sleep

green = LED(17)
red = LED(27)

try:
    while True:
        green.on()
        red.off()
        sleep(1)

        green.off()
        red.on()
        sleep(1)

except KeyboardInterrupt:
    green.off()
    red.off()
