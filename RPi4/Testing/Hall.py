import RPi.GPIO as GPIO
import time
import board, neopixel

H_OUT = [10, 9, 11, 5, 6, 13, 19, 26]
H_IN = 21
LED_PIN = board.D18

# setup hall matrix
GPIO.setmode(GPIO.BCM)
pin = H_IN
GPIO.setup(pin, GPIO.OUT)
GPIO.output(pin, GPIO.LOW)

for pin in H_OUT:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

while True:
        pin_in = H_IN
        GPIO.output(pin_in, GPIO.HIGH)
        time.sleep(0.01)
        values = [GPIO.input(p) for p in H_OUT]
        print(f"Row : {values}")